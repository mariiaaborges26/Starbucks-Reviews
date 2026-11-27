import os
import re
import flet as ft
import hashlib
from deep_translator import GoogleTranslator

cache_traducoes = {}

def traduzir_comentario(texto, idioma_destino):
    if idioma_destino == "pt" or not texto or texto in ["Sem comentário.", "No comment."]:
        return texto
    chave = (texto, idioma_destino)
    if chave not in cache_traducoes:
        try:
            cache_traducoes[chave] = GoogleTranslator(source="auto", target=idioma_destino).translate(texto)
        except Exception:
            return texto
    return cache_traducoes[chave]

from supabase import create_client, Client

SUPABASE_URL = "https://bnnprbudzqtkbaagoasw.supabase.co"
SUPABASE_KEY = "sb_publishable_h4ztQ1CapJXv_35DP3xcBw_TQ3T347Z"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

TEXTOS = {
    "pt": {
        "user": "Nome de utilizador",
        "pin": "PIN ou Palavra-passe",
        "rec": "Palavra de recuperação (ex: nome do animal)",
        "entrar": "Entrar",
        "criar_conta": "Criar Nova Conta",
        "esqueci": "Esqueci-me da palavra-passe / PIN",
        "err_vazio": "Preencha o nome e a palavra-passe.",
        "verificando": "A verificar...",
        "err_nao_enc": "Utilizador não encontrado. Clique em 'Criar Nova Conta'.",
        "err_pin_inc": "Palavra-passe incorreta!",
        "aviso_rec": "Preencha também a palavra de recuperação e clique novamente em 'Criar Nova Conta'.",
        "err_pass_fraca": "A palavra-passe deve ter mín. 6 caracteres, letras, números e 1 símbolo (ex: !@#$).",
        "err_campos": "Preencha todos os campos corretamente.",
        "rec_titulo": "🔑 Recuperar Acesso",
        "rec_novo_pin": "Nova Palavra-passe",
        "guardar_pin": "Guardar Nova Palavra-passe",
        "voltar_login": "Voltar ao Login",
        "pin_alterado": "Palavra-passe alterada! Já pode entrar.",
        "ola": "Olá",
        "sair": "Sair",
        "escolha_prod": "Escolha o produto Starbucks",
        "add_menu_titulo": "➕ Adicionar Produto ao Menu Global",
        "novo_prod_nome": "Nome da nova bebida/comida",
        "categoria": "Categoria",
        "epoca": "Época",
        "guardar_menu": "Guardar no Menu",
        "fechar": "Fechar",
        "nota": "Nota",
        "opiniao": "A sua opinião",
        "publicar": "Publicar Review",
        "guardar_alt": "Guardar Alterações",
        "cancelar": "Cancelar",
        "pesquisar": "🔍 Pesquisar bebida, comida ou autor...",
        "todas": "Todas",
        "sem_coment": "Sem comentário.",
        "por": "por",
        "err_prod_existe": "Esse produto já existe na lista!",
        "err_esc_prod": "Escolha um produto"
    },
    "en": {
        "user": "Username",
        "pin": "PIN or Password",
        "rec": "Recovery word (e.g., pet's name)",
        "entrar": "Log In",
        "criar_conta": "Create New Account",
        "esqueci": "Forgot password / PIN",
        "err_vazio": "Please enter your username and password.",
        "verificando": "Checking...",
        "err_nao_enc": "User not found. Click 'Create New Account'.",
        "err_pin_inc": "Incorrect password!",
        "aviso_rec": "Also fill in the recovery word and click 'Create New Account' again.",
        "err_pass_fraca": "Password needs min. 6 chars, letters, numbers & 1 symbol (e.g., !@#$).",
        "err_campos": "Please fill in all fields correctly.",
        "rec_titulo": "🔑 Recover Access",
        "rec_novo_pin": "New Password",
        "guardar_pin": "Save New Password",
        "voltar_login": "Back to Login",
        "pin_alterado": "Password updated! You can log in now.",
        "ola": "Hello",
        "sair": "Log Out",
        "escolha_prod": "Choose Starbucks item",
        "add_menu_titulo": "➕ Add Item to Global Menu",
        "novo_prod_nome": "New drink/food name",
        "categoria": "Category",
        "epoca": "Season",
        "guardar_menu": "Save to Menu",
        "fechar": "Close",
        "nota": "Rating",
        "opiniao": "Your review",
        "publicar": "Post Review",
        "guardar_alt": "Save Changes",
        "cancelar": "Cancel",
        "pesquisar": "🔍 Search drink, food, or author...",
        "todas": "All",
        "sem_coment": "No comment.",
        "por": "by",
        "err_prod_existe": "This item is already on the list!",
        "err_esc_prod": "Choose an item"
    }
}

def encriptar_texto(texto):
    return hashlib.sha256(texto.strip().lower().encode()).hexdigest()

def password_segura(pw):
    if len(pw) < 6:
        return False
    tem_letra = bool(re.search(r"[a-zA-Z]", pw))
    tem_numero = bool(re.search(r"\d", pw))
    tem_especial = bool(re.search(r"[^a-zA-Z0-9\s]", pw))
    return tem_letra and tem_numero and tem_especial
def main(page: ft.Page):
    page.title = "Starbucks Reviews"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 450
    page.window_height = 800
    page.padding = 20

    sessao = {"utilizador": None, "idioma": "pt"}
    id_edicao = [None]
    catalogo_produtos = []

    def t(chave):
        return TEXTOS[sessao["idioma"]][chave]

    def mudar_idioma(e):
        sessao["idioma"] = "en" if sessao["idioma"] == "pt" else "pt"
        if sessao["utilizador"]:
            mostrar_ecra_principal()
        else:
            mostrar_ecra_login()

    def botao_idioma():
        label = "🇬🇧 EN" if sessao["idioma"] == "pt" else "🇵🇹 PT"
        return ft.OutlinedButton(label, on_click=mudar_idioma, height=34)

    # --- ECRÃ 1: LOGIN / CRIAR CONTA ---
    campo_user = ft.TextField(border_radius=10)
    campo_pin = ft.TextField(password=True, can_reveal_password=True, border_radius=10)
    campo_seguranca = ft.TextField(border_radius=10, visible=False)
    mensagem_erro = ft.Text(color=ft.Colors.RED_600, size=14)

    def fazer_login(e):
        nome = " ".join(campo_user.value.split())
        pin = campo_pin.value.strip()
        if not nome or not pin:
            mensagem_erro.value = t("err_vazio"); page.update(); return
        mensagem_erro.value = t("verificando"); page.update()
        res = supabase.table("utilizadores").select("*").eq("nome_chave", nome.lower()).execute()
        if not res.data:
            mensagem_erro.value = t("err_nao_enc"); page.update(); return
        if res.data[0]["pin"] != encriptar_texto(pin):
            mensagem_erro.value = t("err_pin_inc"); page.update(); return
        sessao["utilizador"] = res.data[0]["nome_original"]
        campo_pin.value, mensagem_erro.value = "", ""
        mostrar_ecra_principal()

    def criar_conta(e):
        if not campo_seguranca.visible:
            campo_seguranca.visible = True
            mensagem_erro.color = "#00704A"
            mensagem_erro.value = t("aviso_rec")
            page.update(); return

        nome = " ".join(campo_user.value.split())
        pin = campo_pin.value.strip()
        seguranca = campo_seguranca.value.strip()
        mensagem_erro.color = ft.Colors.RED_600

        if not nome or not seguranca:
            mensagem_erro.value = t("err_campos"); page.update(); return
        if not password_segura(pin):
            mensagem_erro.value = t("err_pass_fraca"); page.update(); return

        existe = supabase.table("utilizadores").select("id").eq("nome_chave", nome.lower()).execute()
        if existe.data:
            mensagem_erro.value = f"'{nome}' já está em uso / already taken!"; campo_user.focus(); page.update(); return

        supabase.table("utilizadores").insert({
            "nome_chave": nome.lower(), "nome_original": nome,
            "pin": encriptar_texto(pin), "palavra_seguranca": encriptar_texto(seguranca)
        }).execute()

        sessao["utilizador"] = nome
        campo_pin.value, campo_seguranca.value, mensagem_erro.value = "", "", ""
        campo_seguranca.visible = False
        mostrar_ecra_principal()

    def mostrar_ecra_recuperar(e=None):
        rec_user = ft.TextField(label=t("user"), value=campo_user.value, border_radius=10)
        rec_seg = ft.TextField(label=t("rec"), border_radius=10)
        rec_pin = ft.TextField(label=t("rec_novo_pin"), password=True, can_reveal_password=True, border_radius=10)
        rec_msg = ft.Text(color=ft.Colors.RED_600, size=14)

        def redefinir(ev):
            nome, seg, npin = " ".join(rec_user.value.split()), rec_seg.value.strip(), rec_pin.value.strip()
            if not nome or not seg:
                rec_msg.value = t("err_campos"); page.update(); return
            if not password_segura(npin):
                rec_msg.value = t("err_pass_fraca"); page.update(); return
            res = supabase.table("utilizadores").select("*").eq("nome_chave", nome.lower()).execute()
            if not res.data or res.data[0]["palavra_seguranca"] != encriptar_texto(seg):
                rec_msg.value = t("err_pin_inc"); page.update(); return
            supabase.table("utilizadores").update({"pin": encriptar_texto(npin)}).eq("nome_chave", nome.lower()).execute()
            mensagem_erro.color = "#00704A"; mensagem_erro.value = t("pin_alterado")
            mostrar_ecra_login()

        page.clean()
        page.add(
            ft.Row([ft.Container(expand=True), botao_idioma()]),
            ft.Text(t("rec_titulo"), size=26, weight=ft.FontWeight.BOLD, color="#00704A"),
            rec_user, rec_seg, rec_pin, rec_msg,
            ft.Button(t("guardar_pin"), bgcolor="#00704A", color=ft.Colors.WHITE, width=400, height=45, on_click=redefinir),
            ft.TextButton(t("voltar_login"), on_click=lambda ev: mostrar_ecra_login())
        )
        page.update()

    def mostrar_ecra_login():
        campo_user.label = t("user")
        campo_pin.label = t("pin")
        campo_seguranca.label = t("rec")
        page.clean()
        page.add(
            ft.Row([ft.Container(expand=True), botao_idioma()]),
            ft.Text("☕ Starbucks Reviews", size=28, weight=ft.FontWeight.BOLD, color="#00704A"),
            campo_user, campo_pin, campo_seguranca, mensagem_erro,
            ft.Button(t("entrar"), bgcolor="#00704A", color=ft.Colors.WHITE, width=400, height=45, on_click=fazer_login),
            ft.OutlinedButton(t("criar_conta"), width=400, height=45, on_click=criar_conta),
            ft.TextButton(t("esqueci"), on_click=mostrar_ecra_recuperar)
        )
        page.update()
    # --- ECRÃ 2: CATÁLOGO, PESQUISA, FILTROS E REVIEWS ---
    dropdown_produto = ft.Dropdown(border_radius=10, expand=True)
    novo_prod_nome = ft.TextField(border_radius=10)
    novo_prod_cat = ft.Dropdown(border_radius=10, expand=True, value="Bebida Fria", options=[
        ft.dropdown.Option("Bebida Quente"), ft.dropdown.Option("Bebida Fria"), ft.dropdown.Option("Comida / Pastelaria")
    ])
    novo_prod_epoca = ft.Dropdown(border_radius=10, expand=True, value="Anual", options=[
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
        nome = " ".join(novo_prod_nome.value.split()).title()
        if not nome:
            msg_novo_prod.value = t("err_esc_prod"); page.update(); return
        if any(p["nome"].lower() == nome.lower() for p in catalogo_produtos):
            msg_novo_prod.value = t("err_prod_existe"); page.update(); return
        supabase.table("produtos").insert({"nome": nome, "categoria": novo_prod_cat.value, "epoca": novo_prod_epoca.value}).execute()
        novo_prod_nome.value, msg_novo_prod.value = "", ""
        painel_novo_produto.visible = False
        carregar_catalogo(selecionar_nome=nome)

    txt_add_titulo = ft.Text(weight=ft.FontWeight.BOLD, color="#00704A")
    btn_guardar_menu = ft.Button("Guardar", bgcolor="#00704A", color=ft.Colors.WHITE, on_click=guardar_novo_produto)
    btn_fechar_menu = ft.TextButton("Fechar", on_click=lambda e: setattr(painel_novo_produto, "visible", False) or page.update())


    painel_novo_produto = ft.Container(
        visible=False, bgcolor="#E8F5E9", padding=12, border_radius=10, border=ft.Border.all(1, "#00704A"),
        content=ft.Column([
            txt_add_titulo,
            novo_prod_nome,
            ft.Row([novo_prod_cat, novo_prod_epoca]),
            msg_novo_prod,
            ft.Row([btn_guardar_menu, btn_fechar_menu])
        ], spacing=8)
    )

    nota = ft.Dropdown(border_radius=10, width=130, value="5", options=[
        ft.dropdown.Option("5", "⭐⭐⭐⭐⭐"), ft.dropdown.Option("4", "⭐⭐⭐⭐"),
        ft.dropdown.Option("3", "⭐⭐⭐"), ft.dropdown.Option("2", "⭐⭐"), ft.dropdown.Option("1", "⭐")
    ])
    comentario = ft.TextField(multiline=True, min_lines=1, max_lines=3, border_radius=10)

    barra_pesquisa = ft.TextField(border_radius=10, on_change=lambda e: atualizar_lista())
    filtro_cat = ft.Dropdown(border_radius=10, expand=True, value="Todas", on_select=lambda e: atualizar_lista(), options=[
        ft.dropdown.Option("Todas"), ft.dropdown.Option("Bebida Quente"), ft.dropdown.Option("Bebida Fria"), ft.dropdown.Option("Comida / Pastelaria")
    ])
    filtro_epoca = ft.Dropdown(border_radius=10, expand=True, value="Todas", on_select=lambda e: atualizar_lista(), options=[
        ft.dropdown.Option("Todas"), ft.dropdown.Option("Anual"), ft.dropdown.Option("Sazonal")
    ])

    lista_visual = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

    def iniciar_edicao(rev):
        id_edicao[0] = rev["id"]
        dropdown_produto.value, nota.value = rev["produto"], rev["nota"]
        comentario.value = "" if rev["comentario"] in ["Sem comentário.", "No comment."] else rev["comentario"]
        botao_publicar.text, botao_publicar.bgcolor, botao_cancelar.visible = t("guardar_alt"), "#D97706", True
        page.update()

    def cancelar_edicao(e=None):
        id_edicao[0] = None
        dropdown_produto.value, comentario.value = None, ""
        botao_publicar.text, botao_publicar.bgcolor, botao_cancelar.visible = t("publicar"), "#00704A", False
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
                    ft.Text(f"{info_prod['categoria']} ({info_prod['epoca']}) • {t('por')} {r['utilizador']}", size=12, color=ft.Colors.GREY_700),
                    ft.Text(traduzir_comentario(r["comentario"], sessao["idioma"]), size=14)

                ], spacing=4)
            ))
        page.update()

    def guardar_review(e):
        if not dropdown_produto.value:
            dropdown_produto.error_text = t("err_esc_prod"); page.update(); return
        dropdown_produto.error_text = None
        info_prod = next((p for p in catalogo_produtos if p["nome"] == dropdown_produto.value), {"categoria": "Bebida Fria"})
        dados = {"utilizador": sessao["utilizador"], "produto": dropdown_produto.value, "categoria": info_prod["categoria"], "nota": nota.value, "comentario": comentario.value.strip() or t("sem_coment")}
        if id_edicao[0] is not None:
            supabase.table("reviews").update(dados).eq("id", id_edicao[0]).execute(); cancelar_edicao()
        else:
            supabase.table("reviews").insert(dados).execute(); dropdown_produto.value, comentario.value = None, ""
        atualizar_lista()

    def sair(e):
        cancelar_edicao(); sessao["utilizador"] = None; campo_user.value, campo_pin.value, campo_seguranca.value, mensagem_erro.value = "", "", "", ""; campo_seguranca.visible = False; mostrar_ecra_login()

    botao_publicar = ft.Button("Publicar", bgcolor="#00704A", color=ft.Colors.WHITE, expand=True, height=42, on_click=guardar_review)
    botao_cancelar = ft.Button("Cancelar", bgcolor=ft.Colors.GREY_400, color=ft.Colors.BLACK, height=42, visible=False, on_click=cancelar_edicao)


    def mostrar_ecra_principal():
        dropdown_produto.label = t("escolha_prod")
        txt_add_titulo.value = t("add_menu_titulo")
        novo_prod_nome.label = t("novo_prod_nome")
        novo_prod_cat.label = t("categoria")
        novo_prod_epoca.label = t("epoca")
        btn_guardar_menu.text = t("guardar_menu")
        btn_fechar_menu.text = t("fechar")
        nota.label = t("nota")
        comentario.label = t("opiniao")
        botao_publicar.text = t("guardar_alt") if id_edicao[0] else t("publicar")
        botao_cancelar.text = t("cancelar")
        barra_pesquisa.label = t("pesquisar")
        filtro_cat.label = t("categoria")
        filtro_epoca.label = t("epoca")

        page.clean()
        carregar_catalogo()
        page.add(
            ft.Row([
                ft.Text(f"☕ {t('ola')}, {sessao['utilizador']}!", size=18, weight=ft.FontWeight.BOLD, color="#00704A", expand=True),
                botao_idioma(),
                ft.IconButton(icon=ft.Icons.REFRESH, on_click=lambda e: (carregar_catalogo(), atualizar_lista())),
                ft.TextButton(t("sair"), icon=ft.Icons.LOGOUT, on_click=sair)
            ]),
            ft.Row([dropdown_produto, ft.IconButton(icon=ft.Icons.ADD_CIRCLE, icon_color="#00704A", icon_size=32, on_click=lambda e: setattr(painel_novo_produto, "visible", True) or page.update())]),
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

ft.app(
    target=main,
    view=ft.AppView.WEB_BROWSER,
    host="0.0.0.0",
    port=int(os.environ.get("PORT", 8000)),
    assets_dir=os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
)
