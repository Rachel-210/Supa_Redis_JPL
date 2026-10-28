import json
from flask import Flask, render_template, request, redirect, url_for, flash
from database import get_db_connection, get_redis_connection
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = "chave_secreta_trab_bd"

@app.route('/')
def index():
    """Tela de Relatório de Vendas (Consulta direta ao Supabase)"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT * FROM vw_relatorio_vendas ORDER BY data_venda DESC;")
        vendas = cur.fetchall()
    except Exception as e:
        vendas = []
        flash(f"Erro ao carregar relatório: {e}", "danger")
    finally:
        cur.close()
        conn.close()
    
    return render_template('index.html', vendas=vendas)

@app.route('/produtos')
def produtos():
    """Tela de listagem de produtos utilizando Cache do Redis Cloud"""
    try:
        r = get_redis_connection()
        cache_key = "cache_produtos_lista"
        
        cached_produtos = r.get(cache_key)
        
        if cached_produtos:
            lista_produtos = json.loads(cached_produtos)
            origem_dados = "Redis Cloud (Cache)"
        else:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            try:
                cur.execute("""
                    SELECT p.id, p.nome, p.preco, p.estoque, c.nome as categoria_nome 
                    FROM produtos p 
                    JOIN categorias c ON p.categoria_id = c.id 
                    ORDER BY p.id ASC;
                """)
                lista_produtos = cur.fetchall()
                
                for p in lista_produtos:
                    p['preco'] = float(p['preco'])
                  
                r.setex(cache_key, 60, json.dumps(lista_produtos))
                origem_dados = "Supabase (Banco de Dados)"
            except Exception as e:
                print(f"ERRO NO SUPABASE: {e}")
                lista_produtos = []
                flash(f"Erro ao carregar produtos do banco: {e}", "danger")
            finally:
                cur.close()
                conn.close()
                
    except Exception as e:
        print(f"ERRO NO REDIS (CAHE): {e}")
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT p.id, p.nome, p.preco, p.estoque, c.nome as categoria_nome FROM produtos p JOIN categorias c ON p.categoria_id = c.id ORDER BY p.id ASC;")
        lista_produtos = cur.fetchall()
        for p in lista_produtos:
            p['preco'] = float(p['preco'])
        origem_dados = "Supabase (Fallback por erro no Redis)"
        cur.close()
        conn.close()

    return render_template('produtos.html', produtos=lista_produtos, origem_dados=origem_dados)

@app.route('/venda/nova', methods=('GET', 'POST'))
def nova_venda():
    """Tela para registrar nova venda e invalidar o cache do Redis"""
    
    if request.method == 'POST':
        cliente_id = request.form['cliente_id']
        produto_id = request.form['produto_id']
        quantidade = int(request.form['quantidade'])

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("CALL pr_realizar_venda(%s, %s, %s);", (cliente_id, produto_id, quantidade))
            conn.commit()
            
            r = get_redis_connection()
            r.delete("cache_produtos_lista")
            
            flash("Venda registrada com sucesso e cache atualizado!", "success")
            return redirect(url_for('index'))
        except Exception as e:
            conn.rollback()
            flash(f"Erro ao registrar venda: {e}", "danger")
            return redirect(url_for('nova_venda'))
        finally:
            cur.close()
            conn.close()

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT * FROM clientes ORDER BY nome;")
        clientes = cur.fetchall()
        cur.execute("SELECT * FROM produtos WHERE estoque > 0 ORDER BY nome;")
        lista_produtos = cur.fetchall()
    except Exception as e:
        clientes = []
        lista_produtos = []
        flash(f"Erro ao carregar dados do formulário: {e}", "danger")
    finally:
        cur.close()
        conn.close()

    return render_template('nova_venda.html', clientes=clientes, produtos=lista_produtos)

if __name__ == '__main__':
    app.run(debug=True)