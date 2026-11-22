"""
Módulo de Backup Automático em Background e Restauração de Dados (Xenos PDV).
Executa em thread separada (sem travar a UI) a cada X horas definidas pelo usuário.
Mantém histórico rotativo (mantém os últimos N backups para não encher o disco).
Permite também geração de backup manual e importação/restauração completa de arquivos .zip.
"""
import os
import zipfile
import threading
import time
import json
from datetime import datetime
from tkinter import filedialog, messagebox

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(BASE_DIR, "dados", "xenos.db")
PASTA_BACKUPS_PADRAO = os.path.join(BASE_DIR, "dados", "backups")
ARQUIVO_CFG_BACKUP   = os.path.join(BASE_DIR, "dados", "backup_config.json")

CFG_PADRAO = {
    "ativo": True,
    "intervalo_horas": 2,
    "pasta_destino": PASTA_BACKUPS_PADRAO,
    "max_backups_manter": 15,
    "ultimo_backup": ""
}

_thread_backup = None
_parar_thread = False


def carregar_config_backup() -> dict:
    if not os.path.exists(ARQUIVO_CFG_BACKUP):
        salvar_config_backup(CFG_PADRAO)
        return dict(CFG_PADRAO)

    try:
        with open(ARQUIVO_CFG_BACKUP, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            for k, v in CFG_PADRAO.items():
                if k not in cfg:
                    cfg[k] = v
            return cfg
    except Exception:
        return dict(CFG_PADRAO)


def salvar_config_backup(cfg: dict):
    os.makedirs(os.path.dirname(ARQUIVO_CFG_BACKUP), exist_ok=True)
    with open(ARQUIVO_CFG_BACKUP, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)


def executar_backup_silencioso(pasta_destino=None) -> str:
    """Compacta a base de dados em zip e salva na pasta de destino."""
    if not os.path.exists(DB_PATH):
        return None

    cfg = carregar_config_backup()
    destino = pasta_destino or cfg.get("pasta_destino") or PASTA_BACKUPS_PADRAO
    os.makedirs(destino, exist_ok=True)

    data_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nome_arquivo = f"auto_backup_xenos_{data_str}.zip"
    caminho_final = os.path.join(destino, nome_arquivo)

    try:
        with zipfile.ZipFile(caminho_final, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(DB_PATH, arcname="xenos.db")
            lic_path = os.path.join(BASE_DIR, "dados", "licenca.key")
            if os.path.exists(lic_path):
                zf.write(lic_path, arcname="licenca.key")

        cfg["ultimo_backup"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        salvar_config_backup(cfg)
        limpar_backups_antigos(destino, max_manter=cfg.get("max_backups_manter", 15))
        return caminho_final
    except Exception:
        return None


def criar_backup_manual(parent_window=None) -> str:
    """Abre diálogo para salvar backup em local escolhido pelo usuário."""
    if not os.path.exists(DB_PATH):
        if parent_window:
            messagebox.showerror("Erro", "Banco de dados ainda não inicializado!", parent=parent_window)
        return None

    data_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nome_padrao = f"backup_xenos_pdv_{data_str}.zip"

    caminho_destino = filedialog.asksaveasfilename(
        parent=parent_window,
        title="Salvar Cópia de Segurança (Backup)",
        initialfile=nome_padrao,
        defaultextension=".zip",
        filetypes=[("Arquivo Zip", "*.zip")]
    )

    if not caminho_destino:
        return None

    try:
        with zipfile.ZipFile(caminho_destino, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(DB_PATH, arcname="xenos.db")
            lic_path = os.path.join(BASE_DIR, "dados", "licenca.key")
            if os.path.exists(lic_path):
                zf.write(lic_path, arcname="licenca.key")

        if parent_window:
            messagebox.showinfo("Backup Realizado", f"Cópia de segurança criada com sucesso em:\n{caminho_destino}", parent=parent_window)
        return caminho_destino
    except Exception as ex:
        if parent_window:
            messagebox.showerror("Erro no Backup", f"Falha ao gerar cópia de segurança:\n{str(ex)}", parent=parent_window)
        return None


def restaurar_backup(parent_window=None, on_sucesso=None) -> bool:
    """Abre diálogo para selecionar arquivo de backup (.zip) e restaurar o banco de dados."""
    caminho_zip = filedialog.askopenfilename(
        parent=parent_window,
        title="Selecionar Arquivo de Backup para Restaurar (.zip)",
        filetypes=[("Arquivo Zip de Backup", "*.zip")]
    )

    if not caminho_zip:
        return False

    confirma = messagebox.askyesno(
        "Atenção - Restaurar Dados",
        "A restauração substituirá os dados atuais pelo conteúdo deste arquivo de backup.\n\nDeseja realmente continuar?",
        parent=parent_window
    )
    if not confirma:
        return False

    try:
        with zipfile.ZipFile(caminho_zip, "r") as zf:
            if "xenos.db" not in zf.namelist():
                messagebox.showerror("Arquivo Inválido", "Este arquivo não contém uma base de dados válida do Xenos PDV!", parent=parent_window)
                return False

            os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
            zf.extract("xenos.db", path=os.path.dirname(DB_PATH))

            if "licenca.key" in zf.namelist():
                zf.extract("licenca.key", path=os.path.dirname(DB_PATH))

        messagebox.showinfo("Restauração Concluída", "Banco de dados restaurado com sucesso!", parent=parent_window)
        if on_sucesso:
            on_sucesso()
        return True
    except Exception as ex:
        messagebox.showerror("Erro na Restauração", f"Falha ao restaurar banco de dados:\n{str(ex)}", parent=parent_window)
        return False


def limpar_backups_antigos(pasta: str, max_manter: int = 15):
    try:
        if not os.path.exists(pasta):
            return
        arquivos = [
            os.path.join(pasta, f) for f in os.listdir(pasta)
            if f.startswith("auto_backup_xenos_") and f.endswith(".zip")
        ]
        if len(arquivos) > max_manter:
            arquivos.sort(key=os.path.getmtime)
            excluir = arquivos[:len(arquivos) - max_manter]
            for a in excluir:
                try: os.remove(a)
                except Exception: pass
    except Exception:
        pass


def _loop_backup_background():
    global _parar_thread
    time.sleep(60)

    while not _parar_thread:
        cfg = carregar_config_backup()
        if cfg.get("ativo", True):
            intervalo_horas = max(0.5, float(cfg.get("intervalo_horas", 2)))
            intervalo_segundos = intervalo_horas * 3600

            ultimo = cfg.get("ultimo_backup", "")
            fazer = False
            if not ultimo:
                fazer = True
            else:
                try:
                    dt_ultimo = datetime.strptime(ultimo, "%d/%m/%Y %H:%M:%S")
                    passou = (datetime.now() - dt_ultimo).total_seconds()
                    if passou >= intervalo_segundos:
                        fazer = True
                except Exception:
                    fazer = True

            if fazer:
                executar_backup_silencioso()

        for _ in range(60):
            if _parar_thread:
                break
            time.sleep(1)


def iniciar_servico_backup_automatico():
    global _thread_backup, _parar_thread
    if _thread_backup and _thread_backup.is_alive():
        return
    _parar_thread = False
    _thread_backup = threading.Thread(target=_loop_backup_background, daemon=True, name="BackupServiceXenos")
    _thread_backup.start()


def parar_servico_backup():
    global _parar_thread
    _parar_thread = True
