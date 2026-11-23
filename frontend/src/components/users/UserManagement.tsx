import React, { useState, useEffect } from 'react';
import { 
  Users, 
  UserPlus, 
  ShieldCheck, 
  ShieldAlert, 
  Trash2, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  X, 
  AlertCircle,
  RotateCw,
  User as UserIcon,
  Shield
} from 'lucide-react';
import { api } from '../../services/api';
import { User } from '../../types';

interface UserManagementProps {
  currentUser: User | null;
}

export const UserManagement: React.FC<UserManagementProps> = ({ currentUser }) => {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Form State
  const [newUsername, setNewUsername] = useState('');
  const [newDisplayName, setNewDisplayName] = useState('');
  const [newRole, setNewRole] = useState<'ADMIN' | 'OPERATOR'>('OPERATOR');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const showSuccess = (msg: string) => {
    setSuccessMsg(msg);
    setTimeout(() => setSuccessMsg(null), 3000);
  };

  const loadUsers = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await api.getUsers();
      setUsers(data);
    } catch (err: any) {
      setError(err.message || 'Falha ao carregar lista de usuários');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const handleAuthorizeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newUsername.trim()) {
      setError('Por favor, informe o usuário de rede.');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      await api.authorizeUser({
        username: newUsername.trim(),
        display_name: newDisplayName.trim() || undefined,
        role: newRole,
        is_active: true
      });
      showSuccess(`Usuário '${newUsername}' autorizado com sucesso!`);
      setIsModalOpen(false);
      setNewUsername('');
      setNewDisplayName('');
      setNewRole('OPERATOR');
      await loadUsers();
    } catch (err: any) {
      setError(err.message || 'Erro ao autorizar usuário.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleToggleActive = async (targetUser: User) => {
    if (currentUser && targetUser.id === currentUser.id) {
      alert('Você não pode desativar seu próprio acesso de Administrador.');
      return;
    }

    try {
      const res = await api.toggleUserActive(targetUser.id);
      showSuccess(res.message);
      await loadUsers();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleToggleRole = async (targetUser: User) => {
    if (currentUser && targetUser.id === currentUser.id) {
      alert('Você não pode alterar seu próprio papel.');
      return;
    }

    const nextRole = targetUser.role === 'ADMIN' ? 'OPERATOR' : 'ADMIN';
    const confirmMsg = targetUser.role === 'ADMIN'
      ? `Deseja rebaixar '${targetUser.username}' para OPERADOR?`
      : `Deseja promover '${targetUser.username}' para ADMINISTRADOR com acesso total?`;

    if (!window.confirm(confirmMsg)) return;

    try {
      await api.updateUser(targetUser.id, { role: nextRole });
      showSuccess(`Papel do usuário '${targetUser.username}' alterado para ${nextRole}.`);
      await loadUsers();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleDeleteUser = async (targetUser: User) => {
    if (currentUser && targetUser.id === currentUser.id) {
      alert('Você não pode revogar sua própria conta.');
      return;
    }

    if (!window.confirm(`Tem certeza que deseja revogar o acesso do usuário '${targetUser.username}'? Ele não conseguirá mais logar no sistema.`)) {
      return;
    }

    try {
      await api.deleteUser(targetUser.id);
      showSuccess(`Acesso de '${targetUser.username}' revogado.`);
      await loadUsers();
    } catch (err: any) {
      alert(err.message);
    }
  };

  return (
    <div className="space-y-6">
      {/* Mensagem de Sucesso Flutuante */}
      {successMsg && (
        <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold flex items-center space-x-2 animate-fade-in">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Cabeçalho da Página */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-900">
            Usuários & Permissões de Acesso
          </h2>
          <p className="text-xs text-slate-500">
            Gerenciamento de colaboradores do Active Directory autorizados a acessar a plataforma
          </p>
        </div>

        <button
          onClick={() => {
            setError(null);
            setIsModalOpen(true);
          }}
          className="flex items-center space-x-1.5 px-4 py-2 rounded-lg text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 shadow-sm transition-all duration-150 active:scale-98 shrink-0"
        >
          <UserPlus className="w-4 h-4" />
          <span>Autorizar Novo Usuário</span>
        </button>
      </div>

      {/* Quadro Informativo de Segurança */}
      <div className="bg-slate-900 text-slate-300 rounded-xl p-4 border border-slate-800 text-xs shadow-sm flex items-start space-x-3">
        <div className="w-8 h-8 rounded-lg bg-blue-600/20 text-blue-400 flex items-center justify-center shrink-0 mt-0.5">
          <Shield className="w-4 h-4" />
        </div>
        <div className="space-y-1">
          <p className="font-bold text-white">Política de Acesso Corporativo (Whitelist)</p>
          <p className="text-slate-400 leading-relaxed">
            Apenas os colaboradores cadastrados nesta lista conseguem efetuar login com suas credenciais do Active Directory. 
            Usuários com papel de <strong>ADMINISTRADOR</strong> possuem controle total de agendamento e permissões. 
            Usuários com papel de <strong>OPERADOR</strong> possuem acesso para acompanhar logs, execuções e disparar rotinas.
          </p>
        </div>
      </div>

      {/* Tabela de Usuários */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        {isLoading ? (
          <div className="p-12 text-center text-slate-500 text-xs flex items-center justify-center space-x-2">
            <RotateCw className="w-4 h-4 animate-spin text-blue-500" />
            <span>Carregando usuários autorizados...</span>
          </div>
        ) : users.length === 0 ? (
          <div className="p-12 text-center text-slate-500 text-xs">
            Nenhum usuário cadastrado.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="px-5 py-3">Colaborador / Nome</th>
                  <th className="px-5 py-3">Login de Rede (AD)</th>
                  <th className="px-5 py-3">Perfil de Acesso</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3">Último Acesso</th>
                  <th className="px-5 py-3 text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {users.map((u) => {
                  const isSelf = currentUser?.id === u.id;

                  return (
                    <tr key={u.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="px-5 py-3 text-slate-900 font-semibold flex items-center space-x-2.5">
                        <div className="w-7 h-7 rounded-full bg-slate-100 text-slate-600 flex items-center justify-center shrink-0">
                          <UserIcon className="w-3.5 h-3.5" />
                        </div>
                        <span className="truncate max-w-[200px]">{u.display_name || u.username}</span>
                        {isSelf && (
                          <span className="text-[10px] bg-blue-50 text-blue-700 px-1.5 py-0.2 rounded border border-blue-200">
                            Você
                          </span>
                        )}
                      </td>

                      <td className="px-5 py-3 text-slate-600 font-mono">
                        {u.username}
                      </td>

                      <td className="px-5 py-3">
                        <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase tracking-wider border whitespace-nowrap ${
                          u.role === 'ADMIN'
                            ? 'bg-blue-50 text-blue-700 border-blue-200'
                            : 'bg-slate-100 text-slate-700 border-slate-300'
                        }`}>
                          {u.role === 'ADMIN' ? 'Administrador' : 'Operador'}
                        </span>
                      </td>

                      <td className="px-5 py-3">
                        {u.is_active ? (
                          <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center space-x-1 w-max whitespace-nowrap">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                            <span>Ativo</span>
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-rose-50 text-rose-700 border border-rose-200 flex items-center space-x-1 w-max whitespace-nowrap">
                            <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
                            <span>Bloqueado</span>
                          </span>
                        )}
                      </td>

                      <td className="px-5 py-3 text-slate-500 whitespace-nowrap">
                        {u.last_login_at ? new Date(u.last_login_at).toLocaleString('pt-BR') : 'Nunca acessou'}
                      </td>

                      <td className="px-5 py-3 text-right">
                        <div className="flex items-center justify-end space-x-1.5">
                          {/* Alternar Papel */}
                          <button
                            onClick={() => handleToggleRole(u)}
                            disabled={isSelf}
                            title={u.role === 'ADMIN' ? 'Rebaixar para Operador' : 'Promover a Administrador'}
                            className="px-2.5 py-1 rounded text-xs font-semibold border border-slate-300 text-slate-700 hover:bg-slate-100 transition-colors disabled:opacity-40 disabled:cursor-not-allowed whitespace-nowrap"
                          >
                            {u.role === 'ADMIN' ? 'Rebaixar' : 'Promover'}
                          </button>

                          {/* Bloquear / Desbloquear */}
                          <button
                            onClick={() => handleToggleActive(u)}
                            disabled={isSelf}
                            title={u.is_active ? 'Bloquear acesso' : 'Reativar acesso'}
                            className={`px-2.5 py-1 rounded text-xs font-semibold border transition-colors disabled:opacity-40 disabled:cursor-not-allowed whitespace-nowrap ${
                              u.is_active
                                ? 'border-amber-300 text-amber-700 bg-amber-50 hover:bg-amber-100'
                                : 'border-emerald-300 text-emerald-700 bg-emerald-50 hover:bg-emerald-100'
                            }`}
                          >
                            {u.is_active ? 'Bloquear' : 'Ativar'}
                          </button>

                          {/* Excluir Autorização */}
                          <button
                            onClick={() => handleDeleteUser(u)}
                            disabled={isSelf}
                            title="Revogar autorização e excluir da lista"
                            className="p-1.5 rounded text-slate-400 hover:text-rose-600 hover:bg-rose-50 border border-slate-200 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal para Autorizar Novo Usuário */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-white rounded-2xl max-w-md w-full border border-slate-200 shadow-2xl overflow-hidden flex flex-col">
            <div className="px-6 py-4 bg-slate-900 text-white flex items-center justify-between border-b border-slate-800">
              <div className="flex items-center space-x-2">
                <UserPlus className="w-5 h-5 text-blue-400" />
                <h3 className="font-bold text-sm text-white">Autorizar Colaborador do AD</h3>
              </div>
              <button
                onClick={() => setIsModalOpen(false)}
                className="p-1 rounded text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleAuthorizeSubmit} className="p-6 space-y-4">
              {error && (
                <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1">
                  Usuário de Rede (sAMAccountName) *
                </label>
                <input
                  type="text"
                  required
                  placeholder="ex: maria.silva ou USACUCAR2000\maria.silva"
                  value={newUsername}
                  onChange={(e) => setNewUsername(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-lg border border-slate-300 text-sm font-mono text-xs focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600"
                />
                <p className="text-[11px] text-slate-500 mt-1">
                  O colaborador utilizará este login e a própria senha do Windows para entrar.
                </p>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1">
                  Nome Completo / Identificação (Opcional)
                </label>
                <input
                  type="text"
                  placeholder="ex: Maria Silva (Controladoria)"
                  value={newDisplayName}
                  onChange={(e) => setNewDisplayName(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">
                  Perfil de Acesso *
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setNewRole('OPERATOR')}
                    className={`p-2.5 rounded-lg text-xs font-semibold border flex flex-col items-center justify-center space-y-1 transition-all ${
                      newRole === 'OPERATOR'
                        ? 'bg-blue-50 border-blue-500 text-blue-700 shadow-sm'
                        : 'bg-white border-slate-300 text-slate-600 hover:bg-slate-50'
                    }`}
                  >
                    <span className="font-bold">OPERADOR</span>
                    <span className="text-[10px] text-slate-500 font-normal text-center">
                      Visualiza logs, status e executa rotinas
                    </span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setNewRole('ADMIN')}
                    className={`p-2.5 rounded-lg text-xs font-semibold border flex flex-col items-center justify-center space-y-1 transition-all ${
                      newRole === 'ADMIN'
                        ? 'bg-blue-50 border-blue-500 text-blue-700 shadow-sm'
                        : 'bg-white border-slate-300 text-slate-600 hover:bg-slate-50'
                    }`}
                  >
                    <span className="font-bold">ADMINISTRADOR</span>
                    <span className="text-[10px] text-slate-500 font-normal text-center">
                      Controle total, edição e gestão de acessos
                    </span>
                  </button>
                </div>
              </div>

              <div className="pt-3 flex items-center justify-end space-x-2 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-lg text-xs font-semibold text-slate-700 hover:bg-slate-100 border border-slate-300"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2 rounded-lg text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 shadow-sm disabled:opacity-50"
                >
                  {isSubmitting ? 'Autorizando...' : 'Conceder Acesso'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
