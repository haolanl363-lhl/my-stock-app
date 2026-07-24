import React, { useState } from 'react';
import { 
  LayoutDashboard, 
  BookOpen, 
  BarChart3, 
  Settings, 
  PlusCircle, 
  TrendingUp, 
  AlertCircle, 
  HelpCircle,
  ChevronRight,
  ArrowUpRight
} from 'lucide-react';

export default function TradingJournalDashboard() {
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <div className="flex h-screen bg-[#fafafa] text-slate-800 font-sans antialiased">
      {/* 侧边栏 Sidebar */}
      <aside className="w-64 border-r border-slate-200 bg-white p-6 flex flex-col justify-between">
        <div>
          {/* Logo / 系统标题 */}
          <div className="flex items-center gap-3 mb-10">
            <div className="w-8 h-8 rounded-lg bg-slate-900 flex items-center justify-center text-white font-bold text-sm">
              T
            </div>
            <div>
              <h1 className="font-bold text-sm tracking-wide text-slate-900">交易复盘日志</h1>
              <p className="text-xs text-slate-400">TRADING JOURNAL</p>
            </div>
          </div>

          {/* 导航菜单 Navigation */}
          <nav className="space-y-1">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'dashboard' 
                  ? 'bg-slate-100 text-slate-900' 
                  : 'text-slate-500 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              <LayoutDashboard size={18} />
              今日概览
            </button>
            <button
              onClick={() => setActiveTab('logs')}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'logs' 
                  ? 'bg-slate-100 text-slate-900' 
                  : 'text-slate-500 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              <BookOpen size={18} />
              交易记录
            </button>
            <button
              onClick={() => setActiveTab('analytics')}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'analytics' 
                  ? 'bg-slate-100 text-slate-900' 
                  : 'text-slate-500 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              <BarChart3 size={18} />
              统计分析
            </button>
          </nav>
        </div>

        {/* 底部设置 */}
        <div className="border-t border-slate-100 pt-4">
          <button className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-slate-500 hover:bg-slate-50 hover:text-slate-900 transition-colors">
            <Settings size={18} />
            系统设置
          </button>
        </div>
      </aside>

      {/* 主内容区 Main Content */}
      <main className="flex-1 overflow-y-auto p-10">
        {/* 顶部欢迎语 Header */}
        <header className="mb-8">
          <p className="text-xs font-medium text-slate-400 mb-1">
            {new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' })}
          </p>
          <h2 className="text-3xl font-light text-slate-900 tracking-tight">
            下午好，<span className="font-semibold">交易者</span>。
          </h2>
          <p className="text-sm text-slate-500 mt-1">今天保持纪律，每一个决定都是可检索的决策样本。</p>
        </header>

        {/* 核心指标卡片 Data Cards */}
        <div className="grid grid-cols-3 gap-6 mb-8">
          {/* 卡片 1 */}
          <div className="bg-white p-6 rounded-xl border border-slate-200/80 shadow-sm relative overflow-hidden">
            <p className="text-xs font-medium text-slate-400 mb-2">等待下一次交易</p>
            <div className="flex items-baseline gap-2">
              <span className="text-4xl font-light tracking-tight text-slate-900">0</span>
              <span className="text-xs text-slate-400">笔待结算</span>
            </div>
            <p className="text-xs text-slate-500 mt-4 border-t border-slate-100 pt-3">
              纪律第一：宁可错过，也不要犯系统外的错误。
            </p>
          </div>

          {/* 卡片 2 */}
          <div className="bg-white p-6 rounded-xl border border-slate-200/80 shadow-sm">
            <p className="text-xs font-medium text-slate-400 mb-2">本周胜率</p>
            <div className="flex items-baseline gap-2">
              <span className="text-4xl font-light tracking-tight text-slate-900">0.0%</span>
            </div>
            <p className="text-xs text-slate-500 mt-4 border-t border-slate-100 pt-3 flex items-center justify-between">
              <span>近 7 天交易样本</span>
              <span className="text-slate-400">0 胜 0 负</span>
            </p>
          </div>

          {/* 卡片 3 */}
          <div className="bg-white p-6 rounded-xl border border-slate-200/80 shadow-sm">
            <p className="text-xs font-medium text-slate-400 mb-2">净盈亏 (PNL)</p>
            <div className="flex items-baseline gap-1">
              <span className="text-sm font-medium text-slate-400">¥</span>
              <span className="text-4xl font-light tracking-tight text-slate-900">0.00</span>
            </div>
            <p className="text-xs text-slate-500 mt-4 border-t border-slate-100 pt-3">
              当月累计平仓盈亏
            </p>
          </div>
        </div>

        {/* 常用指令 / 快捷入口 Section */}
        <div className="bg-white p-6 rounded-xl border border-slate-200/80 shadow-sm mb-8">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
              完成今日引导
            </h3>
            <button className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-medium transition-colors">
              <PlusCircle size={14} />
              添加交易日志
            </button>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <button className="flex items-center justify-between p-3.5 rounded-lg border border-slate-100 bg-slate-50/50 hover:bg-slate-100/80 text-left transition-colors group">
              <span className="text-xs font-medium text-slate-600 group-hover:text-slate-900">如何记录开仓逻辑？</span>
              <ChevronRight size={14} className="text-slate-400 group-hover:translate-x-0.5 transition-transform" />
            </button>
            <button className="flex items-center justify-between p-3.5 rounded-lg border border-slate-100 bg-slate-50/50 hover:bg-slate-100/80 text-left transition-colors group">
              <span className="text-xs font-medium text-slate-600 group-hover:text-slate-900">如何评估风险收益比？</span>
              <ChevronRight size={14} className="text-slate-400 group-hover:translate-x-0.5 transition-transform" />
            </button>
          </div>
        </div>

        {/* 最近交易记录区域 */}
        <div className="bg-white p-6 rounded-xl border border-slate-200/80 shadow-sm">
          <h3 className="text-sm font-semibold text-slate-800 mb-4">最近决策与交易记录</h3>
          <div className="text-center py-12 border-2 border-dashed border-slate-100 rounded-lg">
            <p className="text-xs text-slate-400 mb-3">今天还没有添加任何交易日志</p>
            <button className="inline-flex items-center gap-2 px-4 py-2 border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-medium rounded-lg transition-colors">
              <PlusCircle size={14} />
              记一笔
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
