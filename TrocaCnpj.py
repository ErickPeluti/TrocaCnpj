import customtkinter as ctk
from tkinter import filedialog, messagebox
import fdb
import os

APP_VERSAO = "0.1.0-alpha"
APP_AUTOR = "Erick Peluti"

# ---------------- CONFIGURAÇÃO VISUAL ----------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ---------------- FIREBIRD DLL ----------------
fdb.load_api(r"C:\Program Files\Firebird\Firebird_2_5\bin\fbclient.dll")
#fdb.load_api("fbclient.dll")

# ---------------- FUNÇÕES ----------------

def validar_documento(texto):
    if texto == "":
        return True

    if not texto.isdigit():
        return False

    return len(texto) <= 14

def testar_conexao():
    caminho = entry_db.get()

    if not caminho or not os.path.exists(caminho):
        messagebox.showwarning("Aviso", "Selecione um banco de dados válido (.FDB)")
        return

    try:
        con = fdb.connect(
            host='localhost',
            database=caminho,
            user='SYSDBA',
            password='masterkey',
            charset='UTF8'
        )
        con.close()
        messagebox.showinfo("Sucesso", "Conexão realizada com sucesso!")
    except Exception as e:
        messagebox.showerror("Erro", str(e))


def trocar_cnpj():
    caminho = entry_db.get()
    documento = entry_cnpj.get().strip()
    ie = entry_ie.get().strip()
    razao = entry_razao.get().strip()

    if not caminho or not os.path.exists(caminho):
        messagebox.showwarning("Aviso", "Selecione o banco de dados")
        return

    if not documento.isdigit() or len(documento) not in (11, 14):
        messagebox.showwarning("Aviso", "Documento inválido (CPF 11 ou CNPJ 14 números)")
        return

    if not ie.isdigit():
        messagebox.showwarning("Aviso", "Inscrição Estadual deve conter apenas números")
        return

    if not razao:
        messagebox.showwarning("Aviso", "Razão Social é obrigatória")
        return

    confirm = messagebox.askyesno(
        "Confirmação",
        "⚠ ATENÇÃO ⚠\n\n"
        "Essa operação irá:\n"
        "- APAGAR dados fiscais\n"
        "- RESETAR NF-e\n"
        "- TROCAR CNPJ/CPF DO EMITENTE\n\n"
        "Backup foi realizado?\n\n"
        "Deseja continuar?",
        icon="warning"
    )

    if not confirm:
        return

    try:
        con = fdb.connect(
            host='localhost',
            database=caminho,
            user='SYSDBA',
            password='masterkey',
            charset='UTF8'
        )

        cur = con.cursor()

        # -------- DELETES FISCAIS --------
        tabelas = [
            "Compra", "Compraxml", "tb_nfe", "tb_nfe_item",
            "tb_nfcompradeposito", "tb_nfedest", "tb_nfe_cartacorrecao"
        ]

        for tabela in tabelas:
            cur.execute(f"DELETE FROM {tabela}")

        # -------- LIMPA NOTAS --------
        cur.execute("""
            UPDATE notas SET
                NFE_XML = NULL,
                OBS = NULL,
                NFE = NULL,
                NFE_SERIE = NULL
        """)

        # -------- ATUALIZA PARAM --------
        cur.execute("""
            UPDATE PARAM SET
                LIBERACAO = NULL,
                ns_Produto = NULL,
                CGC = ?,
                INSC = ?,
                RAZAO_SOCIAL = ?
        """, (documento, ie, razao))

        con.commit()
        con.close()

        messagebox.showinfo("Sucesso", "Troca de documento e reset fiscal concluídos!")

        # -------- LIMPA CAMPOS --------
        entry_cnpj.delete(0, "end")
        entry_ie.delete(0, "end")
        entry_razao.delete(0, "end")
        entry_db.delete(0, "end")
        entry_db.focus()

    except Exception as e:
        try:
            con.rollback()
            con.close()
        except:
            pass
        messagebox.showerror("Erro", str(e))


def escolher_banco():
    caminho = filedialog.askopenfilename(
        title="Selecione o banco de dados",
        filetypes=[("Firebird Database", "*.fdb")]
    )
    if caminho:
        entry_db.delete(0, "end")
        entry_db.insert(0, caminho)


# ---------------- INTERFACE ----------------

app = ctk.CTk()
vcmd_doc = app.register(validar_documento)

app.title("Troca de CNPJ / CPF")
app.geometry("560x520")
app.resizable(False, False)

# ---------- BANCO ----------
ctk.CTkLabel(app, text="Banco de Dados (.FDB):").pack(
    anchor="w", padx=30, pady=(20, 5)
)

frame_db = ctk.CTkFrame(app, fg_color="transparent")
frame_db.pack(anchor="w", padx=30)

entry_db = ctk.CTkEntry(frame_db, width=415)
entry_db.pack(side="left", padx=(0, 10))

ctk.CTkButton(
    frame_db,
    text="Procurar",
    width=80,
    command=escolher_banco
).pack(side="left")

ctk.CTkButton(
    app,
    text="Testar Conexão",
    width=100,
    command=testar_conexao
).pack(anchor="w", padx=30, pady=10)

# ---------- CNPJ / CPF ----------
ctk.CTkLabel(app, text="CNPJ / CPF (somente números):").pack(
    anchor="w", padx=30, pady=(15, 5)
)

entry_cnpj = ctk.CTkEntry(app, width=510, validate="key", validatecommand=(vcmd_doc, "%P"))
entry_cnpj.pack(anchor="w", padx=30)

# ---------- INSCRIÇÃO ESTADUAL ----------
ctk.CTkLabel(app, text="Inscrição Estadual:").pack(
    anchor="w", padx=30, pady=(15, 5)
)

entry_ie = ctk.CTkEntry(app, width=510, validate="key", validatecommand=(vcmd_doc, "%P"))
entry_ie.pack(anchor="w", padx=30)

# ---------- RAZÃO SOCIAL ----------
ctk.CTkLabel(app, text="Razão Social:").pack(
    anchor="w", padx=30, pady=(15, 5)
)

entry_razao = ctk.CTkEntry(app, width=510)
entry_razao.pack(anchor="w", padx=30)

# ---------- BOTÃO EXECUTAR ----------
ctk.CTkButton(
    app,
    text="Executar Troca de CNPJ / CPF",
    fg_color="#C0392B",
    hover_color="#922B21",
    width=300,
    command=trocar_cnpj
).pack(pady=30)

# ---------- AVISO ----------
ctk.CTkLabel(
    app,
    text="⚠ Essa operação apaga dados fiscais. Faça backup antes.",
    text_color="yellow"
).pack(pady=1)

ctk.CTkLabel(
    app,
    text=f"Versão {APP_VERSAO} • feito por {APP_AUTOR}",
    text_color="gray",
    font=("Arial", 11)
).place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-5)

app.mainloop()
