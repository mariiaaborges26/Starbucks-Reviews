import flet as ft
import hashlib
from supabase import create_client, Client

SUPABASE_URL = "https://bnnprbudzqtkbaagoasw.supabase.co"

SUPABASE_KEY = "sb_publishable_h4ztQ1CapJXv_35DP3xcBw_TQ3T347Z"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def encriptar_texto(texto):
    return hashlib.sha256(texto.strip().lower().encode()).hexdigest()

def main(page: ft.Page):
    page.title = "Starbucks Reviews"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 450
    page.window_height = 800
    page.padding = 20

    sessao = {"utilizador": None}
    id_edicao = [None]
    catalogo_produtos = []

    # --- ECRÃ 1: LOGIN / CRIAR CONTA ---
    campo_user = ft.TextField(label="Nome de utilizador", border_radius=10)
    campo_pin = ft.TextField(label="PIN ou Palavra-passe", password=True, can_reveal_password=True, border_radius=10)
    campo_seguranca = ft.TextField(label="Palavra de recuperação (ex: nome do animal)", border_radius=10, visible=False)
    mensagem_erro = ft.Text(color=ft.Colors.RED_600, size=14)

    def fazer_login(e):
        nome = " ".join(campo_user.value.split())
        pin = campo_pin.value.strip()
        if not nome or not pin:
            mensagem_erro.value = "Preencha o nome e o PIN."; page.update(); return
        mensagem_erro.value = "A verificar..."; page.update()
        res = supabase.table("utilizadores").select("*").eq("nome_chave", nome.lower()).execute()
        if not res.data:
            mensagem_erro.value = "Utilizador não encontrado. Clique em 'Criar Nova Conta'."; page.update(); return
        if res.data[0]["pin"] != encriptar_texto(pin):
            mensagem_erro.value = "PIN incorreto!"; page.update(); return
        sessao["utilizador"] = res.data[0]["nome_original"]
        campo_pin.value, mensagem_erro.value = "", ""
        mostrar_ecra_principal()

    def criar_conta(e):
        if not campo_seguranca.visible:
            campo_seguranca.visible = True
            mensagem_erro.color = "#00704A"
            mensagem_erro.value = "Preencha também a palavra de recuperação e clique novamente em 'Criar Nova Conta'."
            page.update(); return

        nome = " ".join(campo_user.value.split())
        pin = campo_pin.value.strip()
        seguranca = campo_seguranca.value.strip()
        mensagem_erro.color = ft.Colors.RED_600

        if not nome or len(pin) < 4 or not seguranca:
            mensagem_erro.value = "Preencha o nome, um PIN (mín. 4 caracteres) e a palavra de recuperação."; page.update(); return

        existe = supabase.table("utilizadores").select("id").eq("nome_chave", nome.lower()).execute()
        if existe.data:
            mensagem_erro.value = f"O nome '{nome}' já está em uso. Escolha outro acima!"; campo_user.focus(); page.update(); return

        supabase.table("utilizadores").insert({
            "nome_chave": nome.lower(), "nome_original": nome,
            "pin": encriptar_texto(pin), "palavra_seguranca": encriptar_texto(seguranca)
        }).execute()

        sessao["utilizador"] = nome
        campo_pin.value, campo_seguranca.value, mensagem_erro.value = "", "", ""
        campo_seguranca.visible = False
        mostrar_ecra_principal()

    def mostrar_ecra_recuperar(e=None):
        rec_user = ft.TextField(label="O seu nome de utilizador", value=campo_user.value, border_radius=10)
        rec_seg = ft.TextField(label="A sua palavra de recuperação", border_radius=10)
        rec_pin = ft.TextField(label="Novo PIN (mín. 4 caracteres)", password=True, can_reveal_password=True, border_radius=10)
        rec_msg = ft.Text(color=ft.Colors.RED_600, size=14)

        def redefinir(ev):
            nome, seg, npin = " ".join(rec_user.value.split()), rec_seg.value.strip(), rec_pin.value.strip()
            if not nome or not seg or len(npin) < 4:
                rec_msg.value = "Preencha todos os campos (PIN mín. 4 caracteres)."; page.update(); return
            res = supabase.table("utilizadores").select("*").eq("nome_chave", nome.lower()).execute()
            if not res.data or res.data[0]["palavra_seguranca"] != encriptar_texto(seg):
                rec_msg.value = "Dados incorretos!"; page.update(); return
            supabase.table("utilizadores").update({"pin": encriptar_texto(npin)}).eq("nome_chave", nome.lower()).execute()
            mensagem_erro.color = "#00704A"; mensagem_erro.value = "PIN alterado! Já pode entrar."
            mostrar_ecra_login()

        page.clean()
        page.add(
            ft.Container(height=30), ft.Text("🔑 Recuperar Acesso", size=26, weight=ft.FontWeight.BOLD, color="#00704A"),
            rec_user, rec_seg, rec_pin, rec_msg,
            ft.Button("Guardar Novo PIN", bgcolor="#00704A", color=ft.Colors.WHITE, width=400, height=45, on_click=redefinir),
            ft.TextButton("Voltar ao Login", on_click=lambda ev: mostrar_ecra_login())
        )
        page.update()

    def mostrar_ecra_login():
        page.clean()
        page.add(
            ft.Container(height=30), ft.Text("☕ Starbucks Reviews", size=28, weight=ft.FontWeight.BOLD, color="#00704A"),
            campo_user, campo_pin, campo_seguranca, mensagem_erro,
            ft.Button("Entrar", bgcolor="#00704A", color=ft.Colors.WHITE, width=400, height=45, on_click=fazer_login),
            ft.OutlinedButton("Criar Nova Conta", width=400, height=45, on_click=criar_conta),
            ft.TextButton("Esqueci-me da palavra-passe / PIN", on_click=mostrar_ecra_recuperar)
        )
        page.update()
    # --- ECRÃ 2: CATÁLOGO, PESQUISA, FILTROS E REVIEWS ---
    dropdown_produto = ft.Dropdown(label="Escolha o produto Starbucks", border_radius=10, expand=True)
    
    # Painel escondido para adicionar produto novo ao menu
    novo_prod_nome = ft.TextField(label="Nome da nova bebida/comida", border_radius=10)
    novo_prod_cat = ft.Dropdown(label="Categoria", border_radius=10, expand=True, value="Bebida Fria", options=[
        ft.dropdown.Option("Bebida Quente"), ft.dropdown.Option("Bebida Fria"), ft.dropdown.Option("Comida / Pastelaria")
    ])
    novo_prod_epoca = ft.Dropdown(label="Época", border_radius=10, expand=True, value="Anual", options=[
        ft.dropdown.Option("Anual"), ft.dropdown.Option("Sazonal")
    ])
    msg_novo_prod = ft.Text(color=ft.Colors.RED_600, size=12)

    def carregar_catalogo(selecionar_nome=None):
        nonlocal catalogo_produtos
        res = supabase.table("produtos").select("*").order("nome").execute()
        catalogo_produtos = res.data
        dropdown_produto.options = [
            ft.dropdown.Option(p["nome"], f"{p['nome']} ({p['epoca']})") for p in catalogo_produtos
        ]
        if selecionar_nome:
            dropdown_produto.value = selecionar_nome
        page.update()

    def guardar_novo_produto(e):
        nome = " ".join(novo_prod_nome.value.split())
        if not nome:
            msg_novo_prod.value = "Escreva o nome do produto."; page.update(); return
        if any(p["nome"].lower() == nome.lower() for p in catalogo_produtos):
            msg_novo_prod.value = "Esse produto já existe na lista!"; page.update(); return
        supabase.table("produtos").insert({"nome": nome, "categoria": novo_prod_cat.value, "epoca": novo_prod_epoca.value}).execute()
        novo_prod_nome.value, msg_novo_prod.value = "", ""
        painel_novo_produto.visible = False
        carregar_catalogo(selecionar_nome=nome)

    painel_novo_produto = ft.Container(
        visible=False, bgcolor="#E8F5E9", padding=12, border_radius=10, border=ft.Border.all(1, "#00704A"),
        content=ft.Column([
            ft.Text("➕ Adicionar Produto ao Menu Global", weight=ft.FontWeight.BOLD, color="#00704A"),
            novo_prod_nome,
            ft.Row([novo_prod_cat, novo_prod_epoca]),
            msg_novo_prod,
            ft.Row([
                ft.Button("Guardar no Menu", bgcolor="#00704A", color=ft.Colors.WHITE, on_click=guardar_novo_produto),
                ft.TextButton("Fechar", on_click=lambda e: setattr(painel_novo_produto, "visible", False) or page.update())
            ])
        ], spacing=8)
    )

    nota = ft.Dropdown(label="Nota", border_radius=10, width=130, value="5", options=[
        ft.dropdown.Option("5", "⭐⭐⭐⭐⭐"), ft.dropdown.Option("4", "⭐⭐⭐⭐"),
        ft.dropdown.Option("3", "⭐⭐⭐"), ft.dropdown.Option("2", "⭐⭐"), ft.dropdown.Option("1", "⭐")
    ])
    comentario = ft.TextField(label="A sua opinião", multiline=True, min_lines=1, max_lines=3, border_radius=10)

    # Barra de Pesquisa e Filtros
    barra_pesquisa = ft.TextField(
        label="🔍 Pesquisar bebida, comida ou autor...", border_radius=10,
        on_change=lambda e: atualizar_lista()
    )
    filtro_cat = ft.Dropdown(label="Categoria", border_radius=10, expand=True, value="Todas", on_select=lambda e: atualizar_lista(), options=[
        ft.dropdown.Option("Todas"), ft.dropdown.Option("Bebida Quente"), ft.dropdown.Option("Bebida Fria"), ft.dropdown.Option("Comida / Pastelaria")
    ])
    filtro_epoca = ft.Dropdown(label="Época", border_radius=10, expand=True, value="Todas", on_select=lambda e: atualizar_lista(), options=[
        ft.dropdown.Option("Todas"), ft.dropdown.Option("Anual"), ft.dropdown.Option("Sazonal")
    ])

    lista_visual = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

    def iniciar_edicao(rev):
        id_edicao[0] = rev["id"]
        dropdown_produto.value, nota.value = rev["produto"], rev["nota"]
        comentario.value = "" if rev["comentario"] == "Sem comentário." else rev["comentario"]
        botao_publicar.text, botao_publicar.bgcolor, botao_cancelar.visible = "Guardar Alterações", "#D97706", True
        page.update()

    def cancelar_edicao(e=None):
        id_edicao[0] = None
        dropdown_produto.value, comentario.value = None, ""
        botao_publicar.text, botao_publicar.bgcolor, botao_cancelar.visible = "Publicar Review", "#00704A", False
        page.update()

    def apagar_review(rid):
        if id_edicao[0] == rid: cancelar_edicao()
        supabase.table("reviews").delete().eq("id", rid).execute()
        atualizar_lista()

    def atualizar_lista(e=None):
        lista_visual.controls.clear()
        nome_logado = sessao["utilizador"].lower()
        termo = barra_pesquisa.value.strip().lower()
        mapa_produtos = {p["nome"]: p for p in catalogo_produtos}

        res = supabase.table("reviews").select("*").order("id", desc=True).execute()
        for r in res.data:
            info_prod = mapa_produtos.get(r["produto"], {"categoria": r["categoria"], "epoca": "Anual"})
            
            # Aplica Pesquisa e Filtros
            if termo and termo not in r["produto"].lower() and termo not in r["utilizador"].lower() and termo not in r["comentario"].lower():
                continue
            if filtro_cat.value != "Todas" and info_prod["categoria"] != filtro_cat.value:
                continue
            if filtro_epoca.value != "Todas" and info_prod["epoca"] != filtro_epoca.value:
                continue

            acoes = ft.Row(spacing=0)
            if r["utilizador"].lower() == nome_logado:
                acoes.controls = [
                    ft.IconButton(icon=ft.Icons.EDIT, icon_color="#00704A", on_click=lambda e, rev=r: iniciar_edicao(rev)),
                    ft.IconButton(icon=ft.Icons.DELETE, icon_color=ft.Colors.RED_600, on_click=lambda e, rid=r["id"]: apagar_review(rid))
                ]
            lista_visual.controls.append(ft.Container(
                bgcolor="#F1F8F5", border=ft.Border.all(1, "#00704A"), border_radius=12, padding=12,
                content=ft.Column([
                    ft.Row([ft.Text(r["produto"], weight=ft.FontWeight.BOLD, size=15, color="#00704A", expand=True), ft.Text("⭐" * int(r["nota"])), acoes]),
                    ft.Text(f"{info_prod['categoria']} ({info_prod['epoca']}) • por {r['utilizador']}", size=12, color=ft.Colors.GREY_700),
                    ft.Text(r["comentario"], size=14)
                ], spacing=4)
            ))
        page.update()

    def guardar_review(e):
        if not dropdown_produto.value:
            dropdown_produto.error_text = "Escolha um produto"; page.update(); return
        dropdown_produto.error_text = None
        info_prod = next((p for p in catalogo_produtos if p["nome"] == dropdown_produto.value), {"categoria": "Bebida Fria"})
        dados = {"utilizador": sessao["utilizador"], "produto": dropdown_produto.value, "categoria": info_prod["categoria"], "nota": nota.value, "comentario": comentario.value.strip() or "Sem comentário."}
        if id_edicao[0] is not None:
            supabase.table("reviews").update(dados).eq("id", id_edicao[0]).execute(); cancelar_edicao()
        else:
            supabase.table("reviews").insert(dados).execute(); dropdown_produto.value, comentario.value = None, ""
        atualizar_lista()

    def sair(e):
        cancelar_edicao(); sessao["utilizador"] = None; campo_user.value, campo_pin.value, campo_seguranca.value, mensagem_erro.value = "", "", "", ""; campo_seguranca.visible = False; mostrar_ecra_login()

    botao_publicar = ft.Button("Publicar Review", bgcolor="#00704A", color=ft.Colors.WHITE, expand=True, height=42, on_click=guardar_review)
    botao_cancelar = ft.Button("Cancelar", bgcolor=ft.Colors.GREY_400, color=ft.Colors.BLACK, height=42, visible=False, on_click=cancelar_edicao)

    def mostrar_ecra_principal():
        page.clean()
        carregar_catalogo()
        page.add(
            ft.Row([ft.Text(f"☕ Olá, {sessao['utilizador']}!", size=20, weight=ft.FontWeight.BOLD, color="#00704A", expand=True), ft.IconButton(icon=ft.Icons.REFRESH, on_click=lambda e: (carregar_catalogo(), atualizar_lista())), ft.TextButton("Sair", icon=ft.Icons.LOGOUT, on_click=sair)]),
            ft.Row([dropdown_produto, ft.IconButton(icon=ft.Icons.ADD_CIRCLE, icon_color="#00704A", icon_size=32, tooltip="Adicionar novo produto ao menu", on_click=lambda e: setattr(painel_novo_produto, "visible", True) or page.update())]),
            painel_novo_produto,
            ft.Row([nota, ft.Container(comentario, expand=True)]),
            ft.Row([botao_publicar, botao_cancelar]),
            ft.Divider(height=15, color="#00704A"),
            barra_pesquisa,
            ft.Row([filtro_cat, filtro_epoca]),
            lista_visual
        )
        atualizar_lista()

    mostrar_ecra_login()

ft.run(main, view=ft.AppView.WEB_BROWSER, port=int(os.environ.get("PORT", 8000)))

