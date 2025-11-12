from src.Application.Controllers.user_controller import UserController
from src.Application.Controllers.produto_controller import ProdutoController
from flask import jsonify, make_response, request, session
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.Infrastructure.http.whats_app import gerar_codigo, verificar_codigo, ultimo_codigo

def init_routes(app):    
    @app.route("/api", methods=["GET"])
    def health():
        return make_response(jsonify({
            "mensagem": "API - OK; Docker - Up",
        }), 200)
    
    @app.route("/send-code", methods=["POST"])
    def send_code():
        try:
            from src.Infrastructure.Model.user import User
            from src.config.data_base import db
            
            data = request.get_json()
            if not data or not data.get("email"):
                return jsonify({"error": "Email é obrigatório"}), 400

            # Gerar e enviar o código primeiro
            codigo = gerar_codigo()

            if not codigo:
                return jsonify({"error": "Falha ao enviar código"}), 500

            print(f"Código gerado e enviado: {codigo}")  # Debug

            # Verificar se o usuário já existe para atualizar, senão cria um novo
            user = db.session.query(User).filter_by(email=data["email"]).first()

            if user:
                # Atualiza o código de validação do usuário existente
                user.codigo_validacao = codigo
                print(f"Atualizando código para usuário existente: {codigo}")  # Debug
            else:
                # Se não existe, cria um novo usuário com os dados básicos
                # status inicial 0 (pendente) até validar código; admin permanecem 2 manualmente
                user = User(
                    name=data.get("name", ""),
                    email=data["email"],
                    password=data.get("password", ""),
                    cnpj="00000000000",
                    celular="11979911839",
                    codigo_validacao=codigo,
                    status=0
                )
                print(f"Criando novo usuário com código: {codigo}")  # Debug
                db.session.add(user)

            db.session.commit()
            return jsonify({"message": "Código enviado com sucesso"}), 200
            
        except Exception as e:
            print(f"Erro ao enviar código: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @app.route("/verify-code", methods=["POST"])
    def verify_code():
        data = request.get_json()
        if not data or "code" not in data or "email" not in data:
            return jsonify({"error": "Código e email são obrigatórios"}), 400
            
        try:
            from src.Infrastructure.Model.user import User
            from src.config.data_base import db
            
            # Buscar usuário e verificar código
            user = db.session.query(User).filter_by(email=data["email"]).first()
            if not user:
                return jsonify({"error": "Usuário não encontrado"}), 404
                
            if not user.codigo_validacao:
                return jsonify({"error": "Nenhum código pendente. Solicite um novo código."}), 400
                
            if data["code"] != user.codigo_validacao:
                return jsonify({"error": "Código incorreto"}), 400
            
            # Atualizar dados do usuário se fornecidos
            if data.get("name"):
                user.name = data["name"]
            if data.get("password"):
                user.password = data["password"]
                
            # Se o código estiver correto, atualiza o status para 1 (usuário comum) se não for admin
            if user.status not in (1,2):
                user.status = 1
            user.codigo_validacao = None
            db.session.commit()
            
            return jsonify({"message": "Código validado com sucesso. Você já pode fazer login."}), 200
            
        except Exception as e:
            print(f"Erro na verificação do código: {str(e)}")
            return jsonify({"error": "Erro ao verificar código"}), 500
        if not data.get("name") or not data.get("email") or not data.get("password"):
                return jsonify({"error": "Dados de cadastro incompletos"}), 400
            
        try:
                # Primeiro verifica se o email já existe
                from src.Infrastructure.Model.user import User
                from src.config.data_base import db
                existing_user = db.session.query(User).filter_by(email=data["email"]).first()
                if existing_user:
                    return jsonify({"error": "Este email já está cadastrado. Por favor, use outro email ou faça login."}), 400
                
                # Se o email não existe, prepara os dados para o registro
                request._cached_json = (dict(
                    name=data["name"],
                    email=data["email"],
                    password=data["password"],
                    cnpj="00000000000",  # valor padrão
                    celular="11979911839"  # número fixo
                ), True)
                
                # Usar o UserController que já tem a lógica de criar usuário
                return UserController.register_user()
                
        except Exception as e:
                print(f"Erro ao criar usuário: {str(e)}")  # log para debug
                if "Duplicate entry" in str(e):
                    return jsonify({"error": "Este email já está cadastrado. Por favor, use outro email ou faça login."}), 400
                return jsonify({"error": "Erro ao criar usuário. Por favor, tente novamente."}), 500
                
        return jsonify({"error": message}), 400
    
    @app.route("/user", methods=["POST"])
    def register_user():
        return UserController.register_user()
    
    @app.route("/user/<int:id>", methods=["GET"])
    @jwt_required()
    def get_user(id):
        return UserController.get_user(id)
    
    @app.route("/verifica", methods=["POST"])
    def verify():
        try:
            data = request.get_json()
            if not data or "email" not in data or "password" not in data:
                return jsonify({"error": "Email e senha são obrigatórios"}), 400

            # Buscar usuário pelo email
            from src.Infrastructure.Model.user import User
            from src.config.data_base import db
            user = db.session.query(User).filter_by(email=data["email"]).first()
            
            if not user:
                return jsonify({"error": "Usuário não encontrado"}), 404
            
            # Verifica a senha (usa o UserController que retorna (response, status) ou Response)
            result = UserController.verify_user()

            # Interpretar o resultado para obter o status code de forma segura
            status_code = None
            try:
                if isinstance(result, tuple):
                    # result normalmente é (response, status_code)
                    _, status = result
                    if isinstance(status, int):
                        status_code = status
                    else:
                        # Caso incomum: status pode ser um objeto Response
                        status_code = getattr(status, 'status_code', None)
                else:
                    # result pode ser um Response
                    status_code = getattr(result, 'status_code', None)
            except Exception:
                status_code = None

            # Se a verificação for bem sucedida (HTTP 200), NÃO sobrescreve status de admin
            if status_code == 200 and user.status != 2:
                # Mantém usuário comum com status 1; não rebaixa admin
                if user.status not in (1,2):  # Em caso de resíduos booleanos
                    user.status = 1
                db.session.commit()

            return result

        except Exception as e:
            print(f"Erro na verificação: {str(e)}")
            return jsonify({"error": "Erro ao verificar usuário"}), 500
    
    @app.route("/user/<int:id>", methods=["PUT"])
    @jwt_required()
    def update_user(id):
        return UserController.atualiza_user(id)

    @app.route("/me", methods=["GET"])
    @jwt_required()
    def me():
        try:
            from src.Infrastructure.Model.user import User
            from src.config.data_base import db
            ident = get_jwt_identity()
            user = None
            # identity pode ser id (int) ou cnpj (string)
            try:
                user_id = int(ident)
                user = db.session.query(User).filter_by(id=user_id).first()
            except Exception:
                # não é int, tentar por cnpj
                user = db.session.query(User).filter_by(cnpj=str(ident)).first()

            if not user:
                return jsonify({"error": "Usuário não encontrado"}), 404

            return jsonify({
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "status": user.status
            }), 200
        except Exception as e:
            print(f"Erro em /me: {str(e)}")
            return jsonify({"error": "Erro ao obter usuário"}), 500
    
    @app.route("/verifica/code", methods=["POST"])
    def validation_code():
        return UserController.validate_code()

    @app.route("/user/<int:id>", methods=["DELETE"])
    @jwt_required()
    def delete_user(id):
        return UserController.delete_user(id)
    
    @app.route("/produto", methods=["POST"])
    def criar_produto():
        return ProdutoController.register_produto()
    
    @app.route("/produto", methods=["GET"])
    def listar():
        return ProdutoController.list_product()
    
    @app.route("/produto/<int:id>", methods=["GET"])
    def get_produto(id):
        return ProdutoController.get_produto(id)
    
    @app.route("/produto/<int:id>", methods=["PUT"])
    def att_produto(id):
        return ProdutoController.att_produto(id)
    
    @app.route("/ativar/<int:id>", methods=["PATCH"])
    def ativar_product(id):
        return ProdutoController.ativar_produto(id)
    
    @app.route("/desativar/<int:id>", methods=["PATCH"])
    def desativar_product(id):
        return ProdutoController.inativar_produto(id)
    
    @app.route("/produto/<int:id>", methods=["DELETE"])
    def exclusao_produto(id):
        return ProdutoController.deletar_produto(id)
    
    @app.route("/produto/vender/<int:id>", methods=["PATCH"])
    def vender_produto(id):
        return ProdutoController.vender(id)

    # ----- Admin stats dashboard -----
    @app.route('/admin/stats', methods=['GET'])
    @jwt_required()
    def admin_stats():
        try:
            from sqlalchemy import func
            from src.Infrastructure.Model.user import User
            from src.Infrastructure.Model.produto import Produto
            from src.Infrastructure.Model.order import Order
            from src.Infrastructure.Model.order_item import OrderItem
            from src.config.data_base import db

            # Verifica admin
            ident = get_jwt_identity()
            user = None
            try:
                uid = int(ident)
                user = db.session.query(User).filter_by(id=uid).first()
            except Exception:
                user = db.session.query(User).filter_by(cnpj=str(ident)).first()
            if not user or user.status != 2:
                return jsonify({"error": "Acesso negado"}), 403

            total_revenue = db.session.query(func.coalesce(func.sum(Order.total), 0.0)).scalar() or 0.0
            total_orders = db.session.query(func.count(Order.id)).scalar() or 0
            total_items_sold = db.session.query(func.coalesce(func.sum(OrderItem.quantity), 0)).scalar() or 0
            stock_total = db.session.query(func.coalesce(func.sum(Produto.quantidade), 0)).scalar() or 0
            
            # Estatísticas adicionais
            unique_customers = db.session.query(func.count(func.distinct(Order.user_id))).scalar() or 0
            avg_order_value = float(total_revenue / total_orders) if total_orders > 0 else 0.0
            total_products = db.session.query(func.count(Produto.id)).scalar() or 0
            products_out_of_stock = db.session.query(func.count(Produto.id)).filter(Produto.quantidade == 0).scalar() or 0
            low_stock_count = db.session.query(func.count(Produto.id)).filter(Produto.quantidade > 0, Produto.quantidade <= 5).scalar() or 0
            
            # Top 5 produtos mais vendidos
            top_selling = (
                db.session.query(
                    Produto.nome,
                    func.coalesce(func.sum(OrderItem.quantity), 0).label('qty')
                )
                .outerjoin(OrderItem, OrderItem.product_id == Produto.id)
                .group_by(Produto.id)
                .order_by(func.coalesce(func.sum(OrderItem.quantity), 0).desc())
                .limit(5)
                .all()
            )
            top_products = [{'name': name, 'quantity': int(qty or 0)} for name, qty in top_selling]
            
            # Produtos com estoque crítico
            low_stock_products = (
                db.session.query(Produto.nome, Produto.quantidade)
                .filter(Produto.quantidade > 0, Produto.quantidade <= 5)
                .order_by(Produto.quantidade.asc())
                .limit(10)
                .all()
            )
            low_stock_list = [{'name': name, 'stock': int(qty)} for name, qty in low_stock_products]

            # Por produto
            rows = (
                db.session.query(
                    Produto.id,
                    Produto.nome,
                    Produto.preco,
                    Produto.quantidade.label('stock'),
                    func.coalesce(func.sum(OrderItem.quantity), 0).label('sold_qty'),
                    func.coalesce(func.sum(OrderItem.line_total), 0.0).label('revenue')
                )
                .outerjoin(OrderItem, OrderItem.product_id == Produto.id)
                .group_by(Produto.id)
                .all()
            )

            per_product = []
            for r in rows:
                sold = int(r.sold_qty or 0)
                stock = int(r.stock or 0)
                price = float(r.preco or 0.0)
                denom = sold + stock
                total_items_float = float(total_items_sold) if total_items_sold else 1.0
                stock_value = float(stock) * price
                per_product.append({
                    'id': r.id,
                    'name': r.nome,
                    'price': price,
                    'sold_qty': sold,
                    'stock_remaining': stock,
                    'stock_value': stock_value,
                    'revenue': float(r.revenue or 0.0),
                    'percent_of_total_sold': (float(sold) / total_items_float * 100.0) if total_items_sold else 0.0,
                    'sold_vs_stock_percent': (float(sold) / float(denom) * 100.0) if denom else 0.0
                })

            # Série por dia
            revenue_by_day = (
                db.session.query(func.date(Order.created_at).label('day'), func.coalesce(func.sum(Order.total), 0.0))
                .group_by(func.date(Order.created_at))
                .order_by(func.date(Order.created_at))
                .all()
            )
            revenue_by_day = [
                { 'date': str(day), 'total': float(total) }
                for day, total in revenue_by_day
            ]

            return jsonify({
                'total_revenue': float(total_revenue),
                'total_orders': int(total_orders),
                'total_items_sold': int(total_items_sold),
                'stock_total': int(stock_total),
                'unique_customers': int(unique_customers),
                'avg_order_value': float(avg_order_value),
                'total_products': int(total_products),
                'products_out_of_stock': int(products_out_of_stock),
                'low_stock_count': int(low_stock_count),
                'top_products': top_products,
                'low_stock_list': low_stock_list,
                'per_product': per_product,
                'revenue_by_day': revenue_by_day
            })
        except Exception as e:
            print(f"Erro ao montar stats: {e}")
            return jsonify({"error": "Falha ao obter estatísticas"}), 500

    # ----- Carrinho em memória simples (sessionStorage front; backend só processa compra) -----
    @app.route('/checkout', methods=['POST'])
    @jwt_required()
    def checkout():
        try:
            from src.Infrastructure.Model.produto import Produto
            from src.Infrastructure.Model.order import Order
            from src.Infrastructure.Model.order_item import OrderItem
            from src.config.data_base import db
            from flask import current_app
            import os
            data = request.get_json() or {}
            items = data.get('items', [])  # [{product_id, quantity}]
            if not items:
                return jsonify({'error': 'Nenhum item enviado', 'code': 'EMPTY_ITEMS'}), 400

            ident = get_jwt_identity()
            user_id = None
            try:
                user_id = int(ident)
            except Exception:
                # se identity não for id direto, tentar mapear via cnpj
                from src.Infrastructure.Model.user import User
                u = db.session.query(User).filter_by(cnpj=str(ident)).first()
                if not u:
                    return jsonify({'error': 'Usuário inválido'}), 400
                user_id = u.id

            order = Order(user_id=user_id, total=0.0)
            db.session.add(order)
            total = 0.0
            for idx, entry in enumerate(items):
                try:
                    pid = int(entry.get('product_id'))
                except Exception:
                    return jsonify({'error': f'product_id inválido no índice {idx}', 'code': 'BAD_PRODUCT_ID'}), 400
                try:
                    qty = int(entry.get('quantity', 1))
                except Exception:
                    return jsonify({'error': f'quantity inválida no índice {idx}', 'code': 'BAD_QUANTITY'}), 400
                produto = db.session.query(Produto).filter_by(id=pid).first()
                if not produto or not produto.status:
                    return jsonify({'error': f'Produto {pid} inválido/inativo', 'code': 'PRODUCT_INACTIVE'}), 400
                if produto.quantidade < qty:
                    return jsonify({'error': f'Estoque insuficiente para produto {pid}', 'code': 'LOW_STOCK'}), 400
                linha_total = produto.preco * qty
                oi = OrderItem(order=order,
                               product_id=produto.id,
                               product_name=produto.nome,
                               unit_price=produto.preco,
                               quantity=qty,
                               line_total=linha_total)
                db.session.add(oi)
                total += linha_total
                # baixa estoque
                produto.quantidade -= qty
            order.total = total
            db.session.commit()
            # Nota fiscal simples (mock JSON)
            nota = {
                'order_id': order.id,
                'user_id': order.user_id,
                'total': order.total,
                'itens': [i.to_dict() for i in order.items]
            }

            # Geração de PDF
            try:
                from reportlab.lib.pagesizes import A4
                from reportlab.pdfgen import canvas
                from reportlab.lib.units import mm
                from src.Infrastructure.Model.user import User
                
                # Buscar nome do usuário
                usuario = db.session.query(User).filter_by(id=order.user_id).first()
                nome_usuario = usuario.name if usuario else f"ID: {order.user_id}"
                
                pdf_dir = os.path.join(current_app.root_path, 'static', 'invoices')
                os.makedirs(pdf_dir, exist_ok=True)
                pdf_path = os.path.join(pdf_dir, f'invoice_{order.id}.pdf')
                c = canvas.Canvas(pdf_path, pagesize=A4)
                width, height = A4
                y = height - 20*mm
                c.setFont("Helvetica-Bold", 14)
                c.drawString(20*mm, y, f"Nota Fiscal - Pedido #{order.id}")
                y -= 10*mm
                c.setFont("Helvetica", 11)
                c.drawString(20*mm, y, f"Usuário: {nome_usuario}")
                y -= 6*mm
                c.drawString(20*mm, y, f"Total: R$ {order.total:.2f}")
                y -= 10*mm
                c.setFont("Helvetica-Bold", 12)
                c.drawString(20*mm, y, "Itens")
                y -= 8*mm
                c.setFont("Helvetica", 10)
                for it in order.items:
                    if y < 20*mm:
                        c.showPage()
                        y = height - 20*mm
                        c.setFont("Helvetica", 10)
                    line = f"{it.product_name} | Qtd: {it.quantity} | Unit: R$ {it.unit_price:.2f} | Total: R$ {it.line_total:.2f}"
                    c.drawString(20*mm, y, line)
                    y -= 6*mm
                c.showPage()
                c.save()
                nota_pdf_url = f"/static/invoices/invoice_{order.id}.pdf"
            except Exception as e_pdf:
                nota_pdf_url = None
                print('Falha ao gerar PDF da nota fiscal:', e_pdf)

            return jsonify({'message': 'Compra realizada', 'nota_fiscal': nota, 'nota_fiscal_url': nota_pdf_url}), 201
        except Exception as e:
            import traceback
            print('Erro no checkout:', e)
            traceback.print_exc()
            return jsonify({'error': 'Falha no checkout', 'detail': str(e), 'code': 'CHECKOUT_EXCEPTION'}), 500

    @app.route('/historico', methods=['GET'])
    @jwt_required()
    def historico():
        try:
            from src.Infrastructure.Model.order import Order
            from src.config.data_base import db
            ident = get_jwt_identity()
            user_id = None
            try:
                user_id = int(ident)
            except Exception:
                from src.Infrastructure.Model.user import User
                u = db.session.query(User).filter_by(cnpj=str(ident)).first()
                if not u:
                    return jsonify({'error': 'Usuário inválido'}), 400
                user_id = u.id
            orders = db.session.query(Order).filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
            return jsonify([o.to_dict(include_items=True) for o in orders]), 200
        except Exception as e:
            print('Erro ao recuperar histórico:', e)
            return jsonify({'error': 'Falha ao recuperar histórico'}), 500

    return app
