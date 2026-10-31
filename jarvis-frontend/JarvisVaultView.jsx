import { useState } from 'react';
import {
  Activity,
  ArrowDownToLine,
  ArrowRightLeft,
  ArrowUpRight,
  Bot,
  CheckCircle2,
  ChevronRight,
  CircleDot,
  Clock3,
  Cpu,
  Database,
  HardDrive,
  Info,
  LayoutDashboard,
  LockKeyhole,
  Mic,
  Plus,
  Settings2,
  ShieldAlert,
  ShieldCheck,
  Wallet,
  WifiOff,
  X,
} from 'lucide-react';
import {
  INITIAL_BALANCES,
  applyDemoVaultAction,
  formatINR,
  getVaultSummary,
  parseRupeesToPaise,
} from './vault-finance.js';

const WALLET_CONFIG = [
  {
    id: 'parents',
    title: 'Parents Vault',
    balanceKey: 'parentsPaise',
    status: 'HARD LOCK',
    description: 'Family funds, protected from ordinary spending.',
    rule: 'Locked for ordinary spending. Allocation changes require an explicit local demo action.',
    Icon: LockKeyhole,
    accent: 'amber',
  },
  {
    id: 'ration',
    title: 'Ration & Food',
    balanceKey: 'rationPaise',
    status: 'RESERVED',
    description: 'Set aside for essential needs.',
    rule: 'Reserved for essentials. Ordinary spend actions use Pocket Money only.',
    Icon: Wallet,
    accent: 'cyan',
  },
  {
    id: 'pocket',
    title: 'Pocket Money',
    balanceKey: 'pocketPaise',
    status: 'LIQUID',
    description: 'Available spending allocation.',
    rule: 'Demo spending is limited to the current available balance.',
    Icon: ShieldCheck,
    accent: 'emerald',
  },
];

const INITIAL_ACTIVITY = [
  {
    id: 'demo-allocation',
    title: 'Funds allocated',
    amountPaise: 1_000_000,
    direction: 'in',
    kind: 'success',
    detail: 'Initial sample allocation. No transfer occurred.',
    time: 'Today, 9:42 AM',
  },
  {
    id: 'demo-blocked',
    title: 'Spending attempt blocked',
    amountPaise: 650_000,
    direction: 'out',
    kind: 'blocked',
    detail: 'Blocked: Exceeds available balance',
    time: 'Today, 9:18 AM',
  },
  {
    id: 'demo-pocket',
    title: 'Pocket Money allocation',
    amountPaise: 400_000,
    direction: 'in',
    kind: 'success',
    detail: 'Initial sample Pocket Money allocation.',
    time: 'Today, 8:05 AM',
  },
];

const SERVICE_STATUS = [
  { label: 'Financial rules', value: 'Demo mode', Icon: ShieldCheck, tone: 'lime' },
  { label: 'SQLite storage', value: 'Offline', Icon: Database, tone: 'amber' },
  { label: 'Personal Brain / Ollama', value: 'Not connected', Icon: Bot, tone: 'muted' },
  { label: 'Backend connection', value: 'Not connected', Icon: WifiOff, tone: 'muted' },
];

const ACTIONS = [
  { id: 'add', label: 'Add Funds', Icon: Plus, tone: 'lime' },
  { id: 'spend', label: 'Record Spend', Icon: ArrowUpRight, tone: 'neutral' },
  { id: 'allocate', label: 'Allocate', Icon: ArrowRightLeft, tone: 'neutral' },
];

const NAV_ITEMS = [
  { label: 'Overview', Icon: LayoutDashboard },
  { label: 'Vault', Icon: LockKeyhole },
  { label: 'Timeline', Icon: Clock3 },
  { label: 'Settings', Icon: Settings2 },
];

function SectionHeading({ eyebrow, title, action, titleId }) {
  return (
    <div className="mb-3 flex items-end justify-between gap-3">
      <div>
        <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-zinc-500">{eyebrow}</p>
        <h2 id={titleId} className="mt-1 text-[17px] font-semibold tracking-normal text-white">{title}</h2>
      </div>
      {action}
    </div>
  );
}

function CoreHeader() {
  return (
    <header className="flex items-center justify-between gap-3 px-5 pb-5 pt-6 sm:px-6">
      <div className="flex min-w-0 items-center gap-3">
        <div className="grid size-11 shrink-0 place-items-center rounded-2xl border border-lime-300/20 bg-lime-300/[0.08] text-lime-300 shadow-[0_0_24px_rgba(163,230,53,0.08)]">
          <Cpu size={21} strokeWidth={1.7} aria-hidden="true" />
        </div>
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <p className="truncate text-xs font-bold tracking-[0.12em] text-white">JARVIS CORE</p>
            <span className="rounded-md border border-white/10 px-1.5 py-0.5 text-[9px] text-zinc-500">v2.0</span>
          </div>
          <p className="mt-1 text-[9px] font-medium tracking-[0.17em] text-zinc-500">PERSONAL LIFE OS</p>
          <span className="mt-2 inline-flex items-center gap-1.5 rounded-full border border-lime-300/20 bg-lime-300/[0.07] px-2 py-1 text-[9px] font-semibold tracking-[0.1em] text-lime-300">
            <HardDrive size={11} aria-hidden="true" /> LOCAL MODE
          </span>
        </div>
      </div>
      <div className="flex shrink-0 items-center gap-2 rounded-full border border-white/5 bg-white/[0.025] px-2.5 py-2" title="Local demo. Backend services have not been checked.">
        <CircleDot size={13} className="text-zinc-500" aria-hidden="true" />
        <span className="text-[9px] font-medium tracking-[0.08em] text-zinc-400">DEMO MODE</span>
      </div>
    </header>
  );
}

function BalanceOverview({ summary, onAction }) {
  const amounts = [
    { label: 'Protected funds', amount: summary.protectedPaise, accent: 'text-amber-300' },
    { label: 'Essential reserve', amount: summary.reservePaise, accent: 'text-cyan-300' },
    { label: 'Available balance', amount: summary.availablePaise, accent: 'text-emerald-300' },
  ];

  return (
    <section className="rounded-[26px] border border-white/[0.07] bg-[#18181C] p-5 shadow-[0_18px_48px_rgba(0,0,0,0.2)] sm:p-6" aria-labelledby="allocated-title">
      <div className="flex items-center justify-between gap-2">
        <p id="allocated-title" className="text-[10px] font-semibold tracking-[0.16em] text-zinc-400">TOTAL ALLOCATED BALANCE</p>
        <span className="rounded-full border border-amber-300/15 bg-amber-300/[0.06] px-2 py-1 text-[8px] font-semibold tracking-[0.12em] text-amber-200">DEMO DATA</span>
      </div>
      <p className="mt-4 text-[36px] font-semibold leading-none tracking-normal text-white sm:text-[40px]">{formatINR(summary.totalPaise)}</p>
      <p className="mt-2 text-[11px] text-zinc-500">Across your local preview wallets</p>

      <div className="mt-5 grid grid-cols-3 divide-x divide-white/[0.07] border-y border-white/[0.07] py-4">
        {amounts.map((item) => (
          <div key={item.label} className="min-w-0 px-2 first:pl-0 last:pr-0">
            <p className="truncate text-[9px] leading-4 text-zinc-500">{item.label}</p>
            <p className={`mt-1 truncate text-[12px] font-semibold tabular-nums ${item.accent}`}>{formatINR(item.amount)}</p>
          </div>
        ))}
      </div>

      <div className="mt-4 grid grid-cols-3 gap-2">
        {ACTIONS.map(({ id, label, Icon, tone }) => (
          <button
            key={id}
            type="button"
            onClick={() => onAction(id)}
            className={`flex min-h-[68px] flex-col items-center justify-center gap-2 rounded-2xl border px-2 py-2 text-[10px] font-medium transition duration-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-lime-300 ${tone === 'lime' ? 'border-lime-300/20 bg-lime-300/[0.08] text-lime-200 hover:bg-lime-300/[0.13]' : 'border-white/[0.07] bg-white/[0.025] text-zinc-300 hover:border-white/15 hover:bg-white/[0.05]'}`}
          >
            <Icon size={17} aria-hidden="true" />
            <span>{label}</span>
          </button>
        ))}
      </div>
      <p className="mt-3 text-center text-[9px] leading-4 text-zinc-600">Demo actions update this view only. No transfer or payment is made.</p>
    </section>
  );
}

function WalletCarousel({ balances, onSelect }) {
  return (
    <section aria-labelledby="wallets-title">
      <SectionHeading eyebrow="VIRTUAL SUB-WALLETS" title="Your allocations" titleId="wallets-title" action={<span className="text-[9px] text-zinc-600">SWIPE TO EXPLORE</span>} />
      <div className="-mx-5 flex snap-x snap-mandatory gap-3 overflow-x-auto px-5 pb-2 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden sm:-mx-6 sm:px-6" aria-label="Wallets, horizontally scrollable">
        {WALLET_CONFIG.map(({ id, title, balanceKey, status, description, Icon, accent }) => {
          const color = {
            amber: 'border-amber-300/15 bg-amber-300/[0.045] text-amber-200',
            cyan: 'border-cyan-300/15 bg-cyan-300/[0.045] text-cyan-200',
            emerald: 'border-emerald-300/15 bg-emerald-300/[0.045] text-emerald-200',
          }[accent];
          return (
            <button
              key={id}
              type="button"
              onClick={() => onSelect(id)}
              aria-label={`Open ${title} details`}
              className={`group min-w-[82%] snap-start rounded-[24px] border p-4 text-left shadow-[0_12px_30px_rgba(0,0,0,0.14)] transition duration-200 hover:-translate-y-0.5 hover:border-white/15 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-lime-300 ${color}`}
            >
              <div className="flex items-start justify-between gap-3">
                <span className="grid size-10 place-items-center rounded-2xl border border-current/15 bg-black/10"><Icon size={19} aria-hidden="true" /></span>
                <span className="rounded-full border border-current/20 px-2 py-1 text-[8px] font-bold tracking-[0.12em]">{status}</span>
              </div>
              <p className="mt-5 text-[13px] font-semibold text-white">{title}</p>
              <p className="mt-1 text-[10px] leading-4 text-zinc-400">{description}</p>
              <div className="mt-4 flex items-end justify-between gap-3">
                <span className="text-[22px] font-semibold leading-none tabular-nums text-white">{formatINR(balances[balanceKey])}</span>
                <span className="mb-0.5 flex items-center gap-1 text-[9px] text-zinc-500 group-hover:text-white">Details <ChevronRight size={13} aria-hidden="true" /></span>
              </div>
            </button>
          );
        })}
      </div>
    </section>
  );
}

function ProtectionCore({ onOpen }) {
  return (
    <button
      type="button"
      onClick={onOpen}
      aria-label="Open JARVIS Protection Core status details"
      className="w-full rounded-[25px] border border-lime-300/20 bg-[radial-gradient(ellipse_at_top_right,rgba(163,230,53,0.12),transparent_58%),#15191a] p-4 text-left shadow-[0_0_36px_rgba(163,230,53,0.06)] transition hover:border-lime-300/35 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-lime-300 sm:p-5"
    >
      <div className="flex items-start gap-3">
        <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-lime-300 text-[#111114]"><ShieldCheck size={19} aria-hidden="true" /></span>
        <span className="min-w-0 flex-1">
          <span className="flex flex-wrap items-center justify-between gap-2">
            <span className="text-[10px] font-bold tracking-[0.13em] text-lime-200">JARVIS PROTECTION CORE</span>
            <span className="rounded-full border border-lime-200/20 px-2 py-1 text-[8px] font-semibold text-lime-200">LOCAL PREVIEW</span>
          </span>
          <span className="mt-1.5 block text-[10px] leading-4 text-zinc-400">Financial allocation and spending rules are configured locally.</span>
        </span>
      </div>
      <span className="mt-4 grid grid-cols-2 gap-2">
        {SERVICE_STATUS.map(({ label, value, tone, Icon }) => (
          <span key={label} className="flex min-w-0 items-center gap-2 rounded-xl border border-white/[0.06] bg-black/20 px-2.5 py-2">
            <Icon size={13} className={tone === 'lime' ? 'shrink-0 text-lime-300' : tone === 'amber' ? 'shrink-0 text-amber-300' : 'shrink-0 text-zinc-500'} aria-hidden="true" />
            <span className="min-w-0">
              <span className="block truncate text-[8px] text-zinc-500">{label}</span>
              <span className={`mt-0.5 block truncate text-[9px] font-medium ${tone === 'lime' ? 'text-lime-200' : tone === 'amber' ? 'text-amber-200' : 'text-zinc-400'}`}>{value}</span>
            </span>
          </span>
        ))}
      </span>
      <span className="mt-3 flex items-center justify-end gap-1 text-[9px] text-lime-200/80">Protection details <ChevronRight size={13} aria-hidden="true" /></span>
    </button>
  );
}

function ActivityFeed({ activity, onSelect }) {
  return (
    <section aria-labelledby="activity-title">
      <SectionHeading
        eyebrow="SECURITY & ACTIVITY"
        title="Recent activity"
        titleId="activity-title"
        action={<span className="inline-flex items-center gap-1 rounded-full border border-white/[0.07] px-2 py-1 text-[8px] font-semibold tracking-[0.1em] text-zinc-500"><Activity size={11} aria-hidden="true" /> DEMO FEED</span>}
      />
      <div className="overflow-hidden rounded-[22px] border border-white/[0.06] bg-[#18181C]">
        {activity.length === 0 ? (
          <div className="px-4 py-8 text-center">
            <Clock3 size={20} className="mx-auto text-zinc-600" aria-hidden="true" />
            <p className="mt-2 text-xs text-zinc-400">No activity yet</p>
            <p className="mt-1 text-[10px] text-zinc-600">New demo actions will appear here.</p>
          </div>
        ) : activity.map((item, index) => {
          const blocked = item.kind === 'blocked';
          const Icon = blocked ? ShieldAlert : item.direction === 'in' ? ArrowDownToLine : ArrowUpRight;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onSelect(item)}
              className={`flex w-full items-center gap-3 px-3.5 py-3.5 text-left transition hover:bg-white/[0.035] focus-visible:outline focus-visible:outline-2 focus-visible:outline-inset focus-visible:outline-lime-300 ${index ? 'border-t border-white/[0.05]' : ''}`}
              aria-label={`Demo transaction: ${item.title}, ${formatINR(item.amountPaise)}`}
            >
              <span className={`grid size-9 shrink-0 place-items-center rounded-xl ${blocked ? 'bg-red-400/[0.08] text-red-300' : 'bg-emerald-400/[0.08] text-emerald-300'}`}><Icon size={16} aria-hidden="true" /></span>
              <span className="min-w-0 flex-1">
                <span className="flex flex-wrap items-center gap-1.5">
                  <span className="truncate text-[11px] font-medium text-zinc-200">{item.title}</span>
                  <span className="rounded border border-white/[0.07] px-1 py-0.5 text-[7px] font-semibold tracking-[0.09em] text-zinc-600">DEMO</span>
                </span>
                <span className={`mt-1 block truncate text-[9px] ${blocked ? 'text-amber-200/80' : 'text-zinc-500'}`}>{item.detail}</span>
              </span>
              <span className="shrink-0 text-right">
                <span className={`block text-[11px] font-semibold tabular-nums ${blocked ? 'text-red-300' : 'text-emerald-300'}`}>{item.direction === 'in' ? '+' : ''}{formatINR(item.amountPaise)}</span>
                <span className="mt-1 block text-[8px] text-zinc-600">{item.time}</span>
              </span>
            </button>
          );
        })}
      </div>
    </section>
  );
}

function BottomNavigation({ activeTab, onSelect, onVoice }) {
  return (
    <nav aria-label="JARVIS navigation" className="z-10 grid shrink-0 grid-cols-5 items-end border-t border-white/[0.07] bg-[#111114]/95 px-2 pb-[max(10px,env(safe-area-inset-bottom))] pt-2 backdrop-blur-xl">
      {NAV_ITEMS.slice(0, 2).map(({ label, Icon }) => (
        <button key={label} type="button" onClick={() => onSelect(label)} aria-current={activeTab === label ? 'page' : undefined} className={`flex min-h-12 flex-col items-center justify-center gap-1 rounded-xl text-[9px] transition ${activeTab === label ? 'text-lime-300' : 'text-zinc-500 hover:text-zinc-200'}`}>
          <Icon size={17} aria-hidden="true" /><span>{label}</span>
        </button>
      ))}
      <button type="button" onClick={onVoice} aria-label="Voice control demo only; does not record audio" title="Voice control demo only" className="-mt-7 mx-auto grid size-12 place-items-center rounded-2xl border border-lime-200/40 bg-lime-300 text-[#111114] shadow-[0_0_24px_rgba(163,230,53,0.18)] transition hover:-translate-y-0.5 hover:bg-lime-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white">
        <Mic size={19} aria-hidden="true" />
      </button>
      {NAV_ITEMS.slice(2).map(({ label, Icon }) => (
        <button key={label} type="button" onClick={() => onSelect(label)} aria-current={activeTab === label ? 'page' : undefined} className={`flex min-h-12 flex-col items-center justify-center gap-1 rounded-xl text-[9px] transition ${activeTab === label ? 'text-lime-300' : 'text-zinc-500 hover:text-zinc-200'}`}>
          <Icon size={17} aria-hidden="true" /><span>{label}</span>
        </button>
      ))}
    </nav>
  );
}

function DialogFrame({ title, onClose, children }) {
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/75 p-0 backdrop-blur-sm sm:items-center sm:p-4" role="presentation">
      <button type="button" aria-label="Close dialog" onClick={onClose} className="absolute inset-0 cursor-default" />
      <section role="dialog" aria-modal="true" aria-labelledby="vault-dialog-title" className="relative z-10 max-h-[88dvh] w-full max-w-md overflow-y-auto rounded-t-[28px] border border-white/10 bg-[#18181C] p-5 pb-[max(20px,env(safe-area-inset-bottom))] shadow-[0_24px_100px_rgba(0,0,0,0.65)] sm:rounded-[28px] sm:p-6">
        <div className="mb-5 flex items-start justify-between gap-4">
          <div>
            <p className="text-[9px] font-bold tracking-[0.17em] text-lime-300">JARVIS CORE / LOCAL DEMO</p>
            <h2 id="vault-dialog-title" className="mt-2 text-xl font-semibold text-white">{title}</h2>
          </div>
          <button type="button" onClick={onClose} aria-label="Close dialog" className="grid size-9 shrink-0 place-items-center rounded-xl border border-white/[0.08] text-zinc-400 transition hover:bg-white/[0.06] hover:text-white"><X size={17} aria-hidden="true" /></button>
        </div>
        {children}
      </section>
    </div>
  );
}

function ActionDialog({ action, availablePaise, onClose, onSubmit }) {
  const [error, setError] = useState('');
  const actionLabels = { add: 'Add Funds', spend: 'Record Spend', allocate: 'Allocate' };

  function handleSubmit(event) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const amountPaise = parseRupeesToPaise(formData.get('amount'));
    if (!amountPaise) {
      setError('Enter a positive amount with up to two decimal places.');
      return;
    }
    const message = onSubmit({
      type: action,
      amountPaise,
      destination: formData.get('destination'),
    });
    setError(message ?? '');
  }

  return (
    <DialogFrame title={actionLabels[action]} onClose={onClose}>
      <p className="mb-5 rounded-xl border border-amber-300/15 bg-amber-300/[0.05] px-3 py-2.5 text-[10px] leading-5 text-amber-100/80">Demo only. No bank transfer, UPI payment, or real transaction occurs.</p>
      {action === 'spend' && <p className="mb-4 text-[10px] leading-5 text-zinc-400">Spendable now: <strong className="font-semibold text-emerald-300">{formatINR(availablePaise)}</strong>. Protected and reserved allocations are excluded.</p>}
      {action === 'allocate' && <p className="mb-4 text-[10px] leading-5 text-zinc-400">Source: Pocket Money ({formatINR(availablePaise)} available). Allocation moves demo funds between local buckets.</p>}
      <form onSubmit={handleSubmit} className="space-y-4">
        <label className="block">
          <span className="mb-2 block text-[9px] font-semibold tracking-[0.13em] text-zinc-400">AMOUNT (INR)</span>
          <span className="flex items-center rounded-xl border border-white/10 bg-black/20 px-3 focus-within:border-lime-300/40">
            <span className="mr-2 text-sm text-zinc-500">₹</span>
            <input autoFocus type="number" name="amount" min="0.01" step="0.01" inputMode="decimal" required aria-describedby={error ? 'vault-action-error' : undefined} placeholder="0.00" className="h-12 w-full bg-transparent text-sm text-white outline-none placeholder:text-zinc-700" />
          </span>
        </label>
        {action === 'allocate' && (
          <label className="block">
            <span className="mb-2 block text-[9px] font-semibold tracking-[0.13em] text-zinc-400">MOVE TO</span>
            <select name="destination" defaultValue="parents" className="h-12 w-full rounded-xl border border-white/10 bg-[#111114] px-3 text-xs text-white outline-none focus:border-lime-300/40">
              <option value="parents">Parents Vault (protected)</option>
              <option value="ration">Ration &amp; Food (reserved)</option>
            </select>
          </label>
        )}
        {error && <p id="vault-action-error" role="alert" className="rounded-xl border border-red-300/20 bg-red-300/[0.06] px-3 py-2 text-[10px] leading-5 text-red-200">{error}</p>}
        <div className="flex gap-2 pt-1">
          <button type="button" onClick={onClose} className="min-h-11 flex-1 rounded-xl border border-white/[0.08] text-xs font-medium text-zinc-300 transition hover:bg-white/[0.04]">Cancel</button>
          <button type="submit" className="min-h-11 flex-1 rounded-xl bg-lime-300 text-xs font-bold text-[#111114] transition hover:bg-lime-200">Apply to demo</button>
        </div>
      </form>
    </DialogFrame>
  );
}

function DetailsDialog({ panel, balances, onClose }) {
  if (panel.kind === 'wallet') {
    const wallet = WALLET_CONFIG.find((item) => item.id === panel.id);
    const Icon = wallet.Icon;
    return (
      <DialogFrame title={wallet.title} onClose={onClose}>
        <div className="rounded-2xl border border-white/[0.07] bg-black/20 p-4">
          <p className="text-[9px] font-semibold tracking-[0.13em] text-zinc-500">CURRENT ALLOCATION</p>
          <p className="mt-2 text-3xl font-semibold text-white">{formatINR(balances[wallet.balanceKey])}</p>
          <div className="mt-4 flex items-center gap-2 border-t border-white/[0.07] pt-3">
            <Icon size={15} className="text-lime-300" aria-hidden="true" />
            <span className="text-[9px] font-bold tracking-[0.12em] text-lime-200">{wallet.status}</span>
          </div>
        </div>
        <p className="mt-4 text-xs leading-5 text-zinc-300">{wallet.description}</p>
        <div className="mt-4 rounded-2xl border border-white/[0.06] p-3.5">
          <p className="text-[9px] font-semibold tracking-[0.12em] text-zinc-500">SPENDING RULE</p>
          <p className="mt-1.5 text-[10px] leading-5 text-zinc-400">{wallet.rule}</p>
        </div>
        <div className="mt-4 rounded-2xl border border-dashed border-white/10 p-3.5">
          <p className="flex items-center gap-2 text-[9px] font-semibold tracking-[0.1em] text-zinc-500"><Clock3 size={13} aria-hidden="true" /> TRANSACTION HISTORY</p>
          <p className="mt-2 text-[10px] leading-5 text-zinc-600">No wallet-linked history is connected in this demo. Sample activity is shown separately.</p>
        </div>
        <p className="mt-4 text-center text-[9px] text-zinc-600">Preview data only. The backend remains the future source of truth.</p>
      </DialogFrame>
    );
  }

  if (panel.kind === 'transaction') {
    const blocked = panel.item.kind === 'blocked';
    return (
      <DialogFrame title={panel.item.title} onClose={onClose}>
        <div className={`rounded-2xl border p-4 ${blocked ? 'border-amber-300/15 bg-amber-300/[0.04]' : 'border-emerald-300/15 bg-emerald-300/[0.04]'}`}>
          <p className="text-[9px] font-semibold tracking-[0.13em] text-zinc-500">DEMO TRANSACTION</p>
          <p className={`mt-2 text-3xl font-semibold ${blocked ? 'text-amber-200' : 'text-emerald-200'}`}>{panel.item.direction === 'in' ? '+' : ''}{formatINR(panel.item.amountPaise)}</p>
          <p className="mt-2 text-[10px] text-zinc-500">{panel.item.time}</p>
        </div>
        <p className="mt-4 text-xs leading-5 text-zinc-300">{panel.item.detail}</p>
        <p className="mt-4 rounded-xl border border-white/[0.06] px-3 py-2.5 text-[10px] leading-5 text-zinc-500">This sample entry is local UI data and is not a real financial record.</p>
      </DialogFrame>
    );
  }

  if (panel.kind === 'protection') {
    return (
      <DialogFrame title="Protection Core" onClose={onClose}>
        <p className="mb-4 text-xs leading-5 text-zinc-400">Financial allocation and spending rules are configured locally. Service status is not inferred from the local UI.</p>
        <div className="space-y-2">
          {SERVICE_STATUS.map(({ label, value, Icon, tone }) => (
            <div key={label} className="flex items-center gap-3 rounded-xl border border-white/[0.06] bg-black/15 px-3 py-3">
              <Icon size={16} className={tone === 'lime' ? 'text-lime-300' : tone === 'amber' ? 'text-amber-300' : 'text-zinc-500'} aria-hidden="true" />
              <span className="flex-1 text-[10px] text-zinc-300">{label}</span>
              <span className={`text-[9px] font-semibold ${tone === 'lime' ? 'text-lime-200' : tone === 'amber' ? 'text-amber-200' : 'text-zinc-500'}`}>{value}</span>
            </div>
          ))}
        </div>
        <div className="mt-4 rounded-xl border border-lime-300/10 bg-lime-300/[0.04] px-3 py-3 text-[10px] leading-5 text-zinc-400">Demo validation is for interface feedback only. The backend must enforce all financial rules independently.</div>
      </DialogFrame>
    );
  }

  return (
    <DialogFrame title={panel.title} onClose={onClose}>
      <div className="flex gap-3 rounded-2xl border border-white/[0.07] bg-black/20 p-4">
        <Info size={17} className="mt-0.5 shrink-0 text-lime-300" aria-hidden="true" />
        <p className="text-xs leading-5 text-zinc-300">{panel.description}</p>
      </div>
    </DialogFrame>
  );
}

export default function JarvisVaultView() {
  const [balances, setBalances] = useState(INITIAL_BALANCES);
  const [activity, setActivity] = useState(INITIAL_ACTIVITY);
  const [activeTab, setActiveTab] = useState('Vault');
  const [action, setAction] = useState(null);
  const [panel, setPanel] = useState(null);
  const summary = getVaultSummary(balances);

  function submitDemoAction({ type, amountPaise, destination }) {
    // Replace this local reducer with a verified backend adapter when its contract is available.
    const result = applyDemoVaultAction(balances, { type, amountPaise, destination });
    if (result.error) return result.error;

    setBalances(result.balances);
    const destinationTitle = destination === 'parents' ? 'Parents Vault' : 'Ration & Food';
    const entry = {
      id: `local-${Date.now()}-${activity.length}`,
      title: type === 'add' ? 'Funds added to Pocket Money' : type === 'spend' ? 'Demo spend recorded' : `${destinationTitle} allocation`,
      amountPaise,
      direction: 'in',
      kind: type === 'spend' ? 'spend' : 'success',
      detail: type === 'spend' ? 'Local-only spending record. No payment occurred.' : 'Local demo balance update. No transfer occurred.',
      time: 'Just now',
    };
    if (type === 'spend') entry.direction = 'out';
    setActivity((current) => [entry, ...current]);
    setAction(null);
    return null;
  }

  function selectNavigation(label) {
    setActiveTab(label);
    if (label !== 'Vault') {
      setPanel({
        kind: 'notice',
        title: `${label} navigation`,
        description: `This standalone module previews the Financial Vault only. ${label} is a navigation placeholder in this demo.`,
      });
    }
  }

  return (
    <div className="min-h-screen bg-[#0A0A0C] px-3 py-3 text-white sm:px-6 sm:py-6">
      <div className="mx-auto flex h-[calc(100dvh-1.5rem)] min-h-[640px] w-full max-w-md flex-col overflow-hidden rounded-[32px] border border-white/[0.06] bg-[#111114] shadow-[0_32px_120px_rgba(0,0,0,0.7)] sm:h-[calc(100dvh-3rem)] sm:min-h-[680px] sm:rounded-[40px]">
        <main className="min-h-0 flex-1 overflow-y-auto overscroll-contain pb-5 [scrollbar-width:thin] [scrollbar-color:rgba(255,255,255,0.12)_transparent]">
          <CoreHeader />
          <div className="space-y-6 px-5 pb-5 sm:px-6">
            <BalanceOverview summary={summary} onAction={setAction} />
            <WalletCarousel balances={balances} onSelect={(id) => setPanel({ kind: 'wallet', id })} />
            <ProtectionCore onOpen={() => setPanel({ kind: 'protection' })} />
            <ActivityFeed activity={activity} onSelect={(item) => setPanel({ kind: 'transaction', item })} />
            <p className="flex items-center justify-center gap-1.5 pb-1 text-center text-[9px] text-zinc-600"><CheckCircle2 size={12} className="text-zinc-500" aria-hidden="true" />Demo values only. No financial records are saved by this component.</p>
          </div>
        </main>
        <BottomNavigation
          activeTab={activeTab}
          onSelect={selectNavigation}
          onVoice={() => setPanel({ kind: 'notice', title: 'Voice control', description: 'This microphone button is a UI control only. It does not record audio or connect to a voice service.' })}
        />
      </div>

      {action && <ActionDialog action={action} availablePaise={summary.availablePaise} onClose={() => setAction(null)} onSubmit={submitDemoAction} />}
      {panel && <DetailsDialog panel={panel} balances={balances} onClose={() => setPanel(null)} />}
    </div>
  );
}