import React, { useState, useEffect } from 'react';
import { 
  FileSpreadsheet, 
  Lock, 
  User as UserIcon, 
  ArrowRight, 
  AlertCircle, 
  ShieldCheck, 
  RotateCw 
} from 'lucide-react';
import { api } from '../../services/api';
import { User, BootstrapStatus } from '../../types';

interface LoginPageProps {
  onLoginSuccess: (user: User) => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [bootstrap, setBootstrap] = useState<BootstrapStatus | null>(null);

  useEffect(() => {
    // Checa se o primeiro administrador já foi provisionado
    api.getBootstrapStatus()
      .then(status => {
        setBootstrap(status);
        if (!status.bootstrap_completed && status.initial_admin_user) {
          setUsername(status.initial_admin_user);
        }
      })
      .catch(() => null);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError('Por favor, preencha o usuário e a senha de rede.');
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      const res = await api.login(username, password);
      onLoginSuccess(res.user);
    } catch (err: any) {
      setError(err.message || 'Falha ao autenticar no Active Directory da Usina.');
    } finally {
      setIsLoading(false);
    }
  };

  const isBootstrapPending = bootstrap && !bootstrap.bootstrap_completed;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 flex flex-col justify-center items-center p-4 relative font-sans text-slate-100">
      {/* Elementos visuais de fundo sutis */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-md w-full relative z-10 space-y-6">
        {/* Identificação Corporativa */}
        <div className="text-center space-y-2">
          <div className="w-14 h-14 rounded-2xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 mx-auto shadow-xl shadow-blue-500/10">
            <FileSpreadsheet className="w-7 h-7" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Excel Automate VM
          </h1>
          <p className="text-xs text-slate-400">
            Automação de Planilhas Headless & Agendador Resiliente
          </p>
        </div>

        {/* Cartão de Login */}
        <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-800 rounded-2xl p-7 shadow-2xl space-y-5">
          {/* Banner de Primeiro Acesso / Bootstrap se pendente */}
          {isBootstrapPending && (
            <div className="p-3.5 rounded-xl bg-blue-950/60 border border-blue-500/40 text-blue-200 text-xs flex items-start space-x-2.5">
              <ShieldCheck className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <span className="font-bold text-white block">Configuração Inicial de Administrador</span>
                <p className="text-[11px] leading-relaxed text-blue-300">
                  O usuário <strong className="text-white">{bootstrap.initial_admin_user}</strong> definido no ambiente assumirá o perfil de <strong>ADMIN</strong> neste primeiro login validado pelo AD.
                </p>
              </div>
            </div>
          )}

          <div className="border-b border-slate-800 pb-3">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">
              Acesso Corporativo (AD)
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Utilize o mesmo usuário e senha que você usa para entrar no Windows
            </p>
          </div>

          {error && (
            <div className="p-3 rounded-lg bg-rose-950/60 border border-rose-500/50 text-rose-300 text-xs flex items-center space-x-2 animate-fade-in">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Campo Usuário */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                Usuário de Domínio
              </label>
              <div className="relative">
                <UserIcon className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  required
                  placeholder="ex: joaoribeiro ou USACUCAR2000\joaoribeiro"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full pl-9 pr-3.5 py-2.5 rounded-lg bg-slate-950 border border-slate-700 text-sm text-white focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
                />
              </div>
            </div>

            {/* Campo Senha */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                Senha de Rede
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  required
                  placeholder="••••••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-9 pr-3.5 py-2.5 rounded-lg bg-slate-950 border border-slate-700 text-sm text-white focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
                />
              </div>
            </div>

            {/* Botão de Entrar */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 px-4 rounded-lg text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 active:scale-98 shadow-lg shadow-blue-600/20 transition-all duration-150 flex items-center justify-center space-x-2 disabled:opacity-50 mt-2"
            >
              {isLoading ? (
                <>
                  <RotateCw className="w-4 h-4 animate-spin" />
                  <span>Validando no AD...</span>
                </>
              ) : (
                <>
                  <span>Entrar no Sistema</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        </div>

        {/* Rodapé Informativo */}
        <p className="text-center text-[11px] text-slate-500">
          Autenticação corporativa integrada ao servidor <code className="text-slate-400">USA9AD2.usacucar.com.br</code>
        </p>
      </div>
    </div>
  );
};
