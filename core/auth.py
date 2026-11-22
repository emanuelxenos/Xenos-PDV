"""
Autenticação — hash de senha e login.
"""
import hashlib
from core.database import get_session, Usuario, criar_tabelas


def _hash(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()


def login(login_str: str, senha: str):
    """Retorna o objeto Usuario se credenciais corretas, senão None."""
    sess = get_session()
    u = sess.query(Usuario).filter_by(login=login_str.strip(), ativo=True).first()
    sess.close()
    if u and u.senha_hash == _hash(senha):
        return u
    return None


def criar_admin_padrao():
    """Cria usuário admin padrão se não existir nenhum usuário."""
    criar_tabelas()
    sess = get_session()
    if sess.query(Usuario).count() == 0:
        admin = Usuario(
            nome="Administrador",
            login="admin",
            senha_hash=_hash("1234"),
            perfil="admin",
        )
        sess.add(admin)
        sess.commit()
    sess.close()
