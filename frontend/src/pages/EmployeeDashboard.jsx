import React, { useState } from 'react';
import {
  Briefcase,
  CheckCircle2,
  Wrench,
  ClipboardList,
  Plus,
  ShoppingBag,
  RefreshCw,
  BookOpen,
  Calendar,
  ChevronRight,
  ArrowRight,
  X,
  FileText,
  AlertTriangle,
  Info,
  Clock,
  CheckCircle,
  HelpCircle,
  Download,
  HelpCircle as ShieldCheck
} from 'lucide-react';
import { useAssetManager } from '../hooks/useAssetManager';
import { downloadOrOpenGuidelinesPdf } from '../utils/downloadDocument';
import AssetIconBadge from '../components/AssetIcon';

const EmployeeDashboard = () => {
  const {
    currentUser,
    assets,
    repairs,
    activity,
    guidelines,
    announcements,
    addRepair,
    logActivity,
    showToast
  } = useAssetManager();

  // Active Modals state
  const [activeModal, setActiveModal] = useState(null); // 'raise' | 'request' | 'status' | 'guidelines' | 'all_assets' | 'announcements'
  const [selectedRepairId, setSelectedRepairId] = useState(null);

  // Form states for raising a repair request
  const [repairAssetId, setRepairAssetId] = useState('');
  const [repairIssue, setRepairIssue] = useState('');
  const [repairDesc, setRepairDesc] = useState('');
  const [repairPriority, setRepairPriority] = useState('Medium');

  // Form states for requesting a new asset
  const [newAssetType, setNewAssetType] = useState('Laptop');
  const [newAssetReason, setNewAssetReason] = useState('');
  const [newAssetPriority, setNewAssetPriority] = useState('Medium');

  // If session is empty, avoid crashing
  if (!currentUser) return null;

  // Filter items matching current logged-in employee (exclude Desktop)
  const myAssignedAssets = assets.filter(a => a.assignedTo === currentUser.id && a.type !== 'Desktop');
  const myRepairs = repairs.filter(r => r.reportedBy === currentUser.id);

  // Sort repairs so latest is first
  const sortedRepairs = [...myRepairs].sort((a, b) => b.id.localeCompare(a.id));

  // Filter activities logged specifically for this employee's personal asset/ticket timeline
  const myActivities = activity.filter(act => {
    const details = act.details || '';
    const detailsLower = details.toLowerCase();

    // 1. Exclude ALL admin system management actions
    const adminActions = [
      'logged in as admin',
      'as admin',
      'added new employee',
      'deleted asset',
      'deleted employee',
      'updated employee',
      'added category',
      'deleted category',
      'updated category',
      'imported employees',
      'imported assets'
    ];
    if (adminActions.some(action => detailsLower.includes(action))) {
      return false;
    }

    // 2. Must specifically pertain to this employee's name, ID, assigned assets, or repairs
    const mentionsEmployeeName = Boolean(currentUser.name && details.includes(currentUser.name));
    const mentionsEmployeeId = Boolean(currentUser.id && details.includes(currentUser.id));
    const pertainsToMyAsset = myAssignedAssets.some(a => details.includes(a.id));
    const pertainsToMyRepair = myRepairs.some(r => details.includes(r.id));
    const isMySelfServiceAction = act.type === 'Report Fault' || act.type === 'Request Asset';

    return mentionsEmployeeName || mentionsEmployeeId || pertainsToMyAsset || pertainsToMyRepair || isMySelfServiceAction;
  });

  // Metrics calculations
  const totalAssignedCount = myAssignedAssets.length;
  // Active means assigned and not under repair
  const activeCount = myAssignedAssets.filter(a => a.status === 'Assigned').length;
  const openRequestsCount = myRepairs.filter(r => r.status === 'In Progress' || r.status === 'Pending' || r.status === 'Awaiting Parts').length;
  const totalRequestsCount = myRepairs.length;

  const handleRaiseSubmit = (e) => {
    e.preventDefault();
    if (!repairAssetId) {
      showToast("Please select a device.", "error");
      return;
    }
    if (!repairIssue.trim()) {
      showToast("Please enter the issue title.", "error");
      return;
    }

    const newRepair = {
      assetId: repairAssetId,
      reportedBy: currentUser.id,
      issue: repairIssue.trim(),
      description: repairDesc.trim() || `Reported fault: ${repairIssue}`,
      priority: repairPriority,
      assignedTo: "IT Support Team",
      estimatedCompletion: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toLocaleDateString() // 5 days from now
    };

    addRepair(newRepair);
    showToast("Repair request successfully submitted to the IT Support Desk!");

    // Reset form
    setRepairAssetId('');
    setRepairIssue('');
    setRepairDesc('');
    setRepairPriority('Medium');
    setActiveModal(null);
  };

  const handleRequestAssetSubmit = (e) => {
    e.preventDefault();
    if (!newAssetReason.trim()) {
      showToast("Please enter the justification reason.", "error");
      return;
    }

    const targetAssetId = myAssignedAssets[0]?.id || assets[0]?.id || "LT0001";
    const newRepair = {
      assetId: targetAssetId,
      reportedBy: currentUser.id,
      issue: `New Asset Request: ${newAssetType}`,
      description: `Requested new asset type: ${newAssetType}. Priority: ${newAssetPriority}. Justification: ${newAssetReason.trim()}`,
      priority: newAssetPriority,
      assignedTo: "IT Support Team",
      estimatedCompletion: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toLocaleDateString()
    };

    addRepair(newRepair);
    logActivity("Request Asset", `Requested new asset type: ${newAssetType}. Justification: ${newAssetReason}`);
    showToast(`Your request for a new ${newAssetType} has been logged and sent to IT Admin for approval.`);

    setNewAssetReason('');
    setNewAssetType('Laptop');
    setNewAssetPriority('Medium');
    setActiveModal(null);
  };

  const selectedRepairDetails = repairs.find(r => r.id === selectedRepairId);

  return (
    <div className="space-y-8 animate-fade-in font-sans">

      {/* Personalized Welcome Hero Banner */}
      <div className="bg-[#1E3A8A] rounded-3xl p-6 text-white shadow-lg relative overflow-hidden flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="space-y-1.5 z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 backdrop-blur-md text-[11px] font-bold tracking-wide">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>Employee Self-Service Portal</span>
          </div>
          <h2 className="text-xl sm:text-2xl font-black tracking-tight">
            Welcome back, {currentUser?.name || 'Rahul Sharma'} 👋
          </h2>
          <p className="text-xs text-slate-200/90 font-medium">
            Department: <span className="font-bold text-white">{currentUser?.department || 'IT'}</span> &bull; Employee ID: <span className="font-bold text-white">{currentUser?.id || 'EMP001'}</span> &bull; Active Devices: <span className="font-bold text-white">{activeCount}</span>
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5 z-10">
          <button
            onClick={() => setActiveModal('raise')}
            className="px-4 py-2.5 rounded-2xl bg-white text-[#1E3A8A] hover:bg-slate-50 font-bold text-xs shadow-md transition-all flex items-center gap-1.5 cursor-pointer"
          >
            <Wrench className="h-4 w-4 text-[#1E3A8A]" />
            <span>Report Device Fault</span>
          </button>
          <button
            onClick={() => setActiveModal('request')}
            className="px-4 py-2.5 rounded-2xl bg-white/10 hover:bg-white/20 backdrop-blur-md border border-white/20 text-white font-bold text-xs transition-all flex items-center gap-1.5 cursor-pointer"
          >
            <ShoppingBag className="h-4 w-4" />
            <span>Request New Asset</span>
          </button>
        </div>
      </div>

      {/* 4 KPI Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">

        {/* Metric 1 */}
        <div className="bg-white border border-slate-200 rounded-3xl p-5 shadow-sm flex items-center gap-4 hover:shadow-md transition-all">
          <div className="p-4 bg-blue-50 text-blue-600 rounded-2xl">
            <Briefcase className="h-6 w-6" />
          </div>
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Total Assigned Assets</p>
            <h3 className="text-2xl font-black text-slate-800 mt-1">{totalAssignedCount}</h3>
            <p className="text-[10px] text-slate-400 font-semibold mt-1">All assets assigned to you</p>
          </div>
        </div>

        {/* Metric 2 */}
        <div className="bg-white border border-slate-200 rounded-3xl p-5 shadow-sm flex items-center gap-4 hover:shadow-md transition-all">
          <div className="p-4 bg-emerald-50 text-emerald-600 rounded-2xl">
            <CheckCircle className="h-6 w-6" />
          </div>
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Active Assets</p>
            <h3 className="text-2xl font-black text-slate-800 mt-1">{activeCount}</h3>
            <p className="text-[10px] text-slate-400 font-semibold mt-1">Currently in use</p>
          </div>
        </div>

        {/* Metric 3 */}
        <div className="bg-white border border-slate-200 rounded-3xl p-5 shadow-sm flex items-center gap-4 hover:shadow-md transition-all">
          <div className="p-4 bg-amber-50 text-amber-600 rounded-2xl">
            <Wrench className="h-6 w-6" />
          </div>
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Open Requests</p>
            <h3 className="text-2xl font-black text-slate-800 mt-1">{openRequestsCount}</h3>
            <p className="text-[10px] text-slate-400 font-semibold mt-1">Awaiting action</p>
          </div>
        </div>

        {/* Metric 4 */}
        <div className="bg-white border border-slate-200 rounded-3xl p-5 shadow-sm flex items-center gap-4 hover:shadow-md transition-all">
          <div className="p-4 bg-purple-50 text-purple-600 rounded-2xl">
            <ClipboardList className="h-6 w-6" />
          </div>
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Total Requests</p>
            <h3 className="text-2xl font-black text-slate-800 mt-1">{totalRequestsCount}</h3>
            <p className="text-[10px] text-slate-400 font-semibold mt-1">All time requests</p>
          </div>
        </div>

      </div>

      {/* Main Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

        {/* LEFT COLUMN: Assigned Devices & Repair Logs (Span 2) */}
        <div className="lg:col-span-2 space-y-8">

          {/* My Assigned Assets Card */}
          <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-800">My Assigned Assets</h3>
              <button
                onClick={() => setActiveModal('all_assets')}
                className="text-xs font-bold text-blue-600 hover:text-blue-800 transition-all"
              >
                View All
              </button>
            </div>

            <div className="divide-y divide-slate-100 max-h-[360px] overflow-y-auto pr-1">
              {myAssignedAssets.length === 0 ? (
                <p className="text-xs text-slate-400 py-8 text-center">No assets currently assigned to your record.</p>
              ) : (
                myAssignedAssets.slice(0, 5).map(asset => (
                  <div key={asset.id} className="py-3 flex items-center justify-between gap-3 group">
                    <div className="flex items-center gap-3 min-w-0 flex-1">
                      <AssetIconBadge type={asset.type} className="h-10 w-10 rounded-xl shrink-0" iconSize="h-5 w-5" />
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <p className="text-xs font-extrabold text-slate-800 group-hover:text-blue-600 transition-all truncate">{asset.brand} {asset.model}</p>
                          <span className="px-1.5 py-0.5 rounded-md bg-blue-50 text-blue-600 text-[8px] font-extrabold uppercase shrink-0 border border-blue-100/60">
                            {asset.type}
                          </span>
                        </div>
                        <p className="text-[10px] text-slate-400 font-medium mt-0.5 truncate">Asset ID: {asset.id} &bull; Serial No: {asset.serialNumber}</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-4 shrink-0">
                      <div className="text-right w-28 shrink-0 hidden sm:block">
                        <p className="text-[9px] font-extrabold text-slate-400 uppercase tracking-wider">Assigned On</p>
                        <p className="text-[10px] font-bold text-slate-700 mt-0.5">{asset.purchaseDate || '10 May 2024'}</p>
                      </div>
                      <div className="w-24 flex justify-end shrink-0">
                        <span className={`px-2.5 py-1 rounded-full text-[9px] font-extrabold uppercase tracking-wide inline-block text-center min-w-[85px] shadow-2xs ${asset.status === 'Assigned'
                            ? 'bg-blue-50 text-[#1E3A8A] border border-blue-200/60'
                            : 'bg-rose-50 text-rose-600 border border-rose-200/60'
                          }`}>
                          {asset.status === 'Assigned' ? 'Active' : 'Under Repair'}
                        </span>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>

            <button
              onClick={() => setActiveModal('all_assets')}
              className="w-full py-2.5 border border-slate-100 hover:border-blue-500 rounded-2xl flex items-center justify-center gap-1.5 text-xs font-bold text-blue-600 bg-slate-50/50 hover:bg-white hover:shadow-sm transition-all mt-4"
            >
              <span>View All Assets</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>

          {/* Requests Overview Card */}
          <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-800">Requests Overview</h3>
              <button
                onClick={() => setActiveModal('status')}
                className="text-xs font-bold text-blue-600 hover:text-blue-800 transition-all"
              >
                View All
              </button>
            </div>

            <div className="overflow-x-auto pr-1">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-slate-100 text-[9px] font-bold text-slate-400 uppercase tracking-wider">
                    <th className="pb-3 pr-3">Request ID</th>
                    <th className="pb-3 px-3">Issue</th>
                    <th className="pb-3 px-3">Status</th>
                    <th className="pb-3 px-3 text-right">Submitted On</th>
                    <th className="pb-3 pl-3"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50 text-slate-700">
                  {sortedRepairs.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="py-8 text-center text-slate-400">No support requests filed.</td>
                    </tr>
                  ) : (
                    sortedRepairs.slice(0, 3).map(rep => (
                      <tr
                        key={rep.id}
                        onClick={() => { setSelectedRepairId(rep.id); setActiveModal('status'); }}
                        className="hover:bg-slate-50/40 cursor-pointer transition-all"
                      >
                        <td className="py-3 pr-3 font-bold text-slate-500">{rep.id}</td>
                        <td className="py-3 px-3 font-semibold text-slate-800">{rep.issue}</td>
                        <td className="py-3 px-3">
                          <span className={`px-2 py-0.5 rounded-full text-[9px] font-extrabold ${rep.status === 'Resolved' || rep.status === 'Completed' ? 'bg-emerald-50 text-emerald-600' :
                              rep.status === 'In Progress' ? 'bg-amber-50 text-amber-600' :
                                rep.status === 'Cancelled' ? 'bg-slate-100 text-slate-500' : 'bg-blue-50 text-blue-600'
                            }`}>
                            {rep.status}
                          </span>
                        </td>
                        <td className="py-3 px-3 text-right text-slate-500 font-medium">
                          {rep.requestDate.split(' ')[0]}
                        </td>
                        <td className="py-3 pl-3 text-right text-slate-400">
                          <ChevronRight className="h-4 w-4 inline-block" />
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

        </div>

        {/* RIGHT COLUMN: Quick Actions, Announcements, Timeline Activity */}
        <div className="space-y-8">

          {/* Quick Actions (2x2 Grid) */}
          <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-sm space-y-4">
            <h3 className="text-sm font-bold text-slate-800">Quick Actions</h3>
            <div className="grid grid-cols-2 gap-4">

              {/* Action 1 */}
              <button
                onClick={() => setActiveModal('raise')}
                className="p-4 border border-slate-100 hover:border-blue-500 rounded-2xl text-left bg-slate-50/40 hover:bg-white hover:shadow-md hover:shadow-blue-500/5 transition-all space-y-3 group"
              >
                <div className="h-9 w-9 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center group-hover:bg-blue-600 group-hover:text-white transition-all">
                  <Plus className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-xs font-bold text-slate-800">Raise Ticket</p>
                  <p className="text-[9px] text-slate-400 font-medium mt-1 leading-relaxed">Report issues or request support</p>
                </div>
              </button>

              {/* Action 2 */}
              <button
                onClick={() => setActiveModal('request')}
                className="p-4 border border-slate-100 hover:border-blue-500 rounded-2xl text-left bg-slate-50/40 hover:bg-white hover:shadow-md hover:shadow-blue-500/5 transition-all space-y-3 group"
              >
                <div className="h-9 w-9 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center group-hover:bg-emerald-600 group-hover:text-white transition-all">
                  <ShoppingBag className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-xs font-bold text-slate-800">New Ticket</p>
                  <p className="text-[9px] text-slate-400 font-medium mt-1 leading-relaxed">Request new IT equipment</p>
                </div>
              </button>

              {/* Action 3 */}
              <button
                onClick={() => setActiveModal('status')}
                className="p-4 border border-slate-100 hover:border-blue-500 rounded-2xl text-left bg-slate-50/40 hover:bg-white hover:shadow-md hover:shadow-blue-500/5 transition-all space-y-3 group"
              >
                <div className="h-9 w-9 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center group-hover:bg-purple-600 group-hover:text-white transition-all">
                  <RefreshCw className="h-4.5 w-4.5" />
                </div>
                <div>
                  <p className="text-xs font-bold text-slate-800">Check Status</p>
                  <p className="text-[9px] text-slate-400 font-medium mt-1 leading-relaxed">Track your active request tickets</p>
                </div>
              </button>

              {/* Action 4 */}
              <button
                onClick={() => setActiveModal('guidelines')}
                className="p-4 border border-slate-100 hover:border-blue-500 rounded-2xl text-left bg-slate-50/40 hover:bg-white hover:shadow-md hover:shadow-blue-500/5 transition-all space-y-3 group"
              >
                <div className="h-9 w-9 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center group-hover:bg-amber-600 group-hover:text-white transition-all">
                  <BookOpen className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-xs font-bold text-slate-800">IT Guidelines</p>
                  <p className="text-[9px] text-slate-400 font-medium mt-1 leading-relaxed">View company IT assets policies</p>
                </div>
              </button>

            </div>
          </div>

          {/* Recent Announcements */}
          <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-800">Recent Announcements</h3>
              <button
                onClick={() => setActiveModal('announcements')}
                className="text-xs font-bold text-blue-600 hover:text-blue-800 transition-all cursor-pointer"
              >
                View All ({announcements?.length || 0})
              </button>
            </div>

            {(!announcements || announcements.length === 0) ? (
              <p className="text-xs text-slate-400 font-semibold py-3">No active announcements posted.</p>
            ) : (
              announcements.slice(0, 2).map((ann) => (
                <div
                  key={ann.id}
                  onClick={() => setActiveModal('announcements')}
                  className="p-4 bg-slate-50 rounded-2xl border border-slate-100 space-y-2 relative group hover:bg-white hover:border-blue-500 hover:shadow-sm transition-all cursor-pointer"
                >
                  <div className="flex items-start gap-3">
                    <div className="p-2 bg-blue-50 text-blue-600 rounded-xl shrink-0 mt-0.5">
                      <Info className="h-4.5 w-4.5" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h4 className="text-xs font-bold text-slate-800 truncate">{ann.title}</h4>
                        <span className={`px-2 py-0.5 text-[9px] font-extrabold rounded-md border ${ann.priority === 'High' || ann.priority === 'Urgent' ? 'bg-red-50 text-red-600 border-red-200' : 'bg-blue-50 text-blue-600 border-blue-200'
                          }`}>
                          {ann.type || 'General'}
                        </span>
                      </div>
                      <p className="text-[10px] text-slate-400 font-semibold mt-1 line-clamp-2 leading-relaxed">{ann.message}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-1.5 text-[9px] text-slate-400 font-bold pt-2 border-t border-slate-200/50 pl-8">
                    <Calendar className="h-3 w-3" />
                    <span>{ann.date} &bull; {ann.author}</span>
                  </div>
                  <ChevronRight className="absolute right-3 top-[40%] h-4 w-4 text-slate-400 group-hover:translate-x-0.5 transition-all" />
                </div>
              ))
            )}
          </div>

          {/* Recent Activity Timeline */}
          <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-800">Recent Activity</h3>
              <button className="text-xs font-bold text-blue-600 hover:text-blue-800 transition-all">View All</button>
            </div>

            <div className="relative pl-6 space-y-5 border-l border-slate-100 ml-3">
              {myActivities.length === 0 ? (
                <p className="text-[10px] text-slate-400 font-semibold py-4 pl-1">No activities logged yet.</p>
              ) : (
                myActivities.slice(0, 3).map((act, index) => {
                  const isResolve = act.activity.includes("Resolve") || act.details.includes("resolved");
                  const isAssign = act.activity.includes("Assign") || act.details.includes("assigned");

                  return (
                    <div key={act.id} className="relative group">
                      {/* Timeline circle icon indicator */}
                      <span className={`absolute -left-[35px] top-0.5 p-1 rounded-full shrink-0 border-2 border-white ring-4 ring-white ${isResolve ? 'bg-emerald-50 text-emerald-600 ring-emerald-50/50' :
                          isAssign ? 'bg-blue-50 text-blue-600 ring-blue-50/50' : 'bg-amber-50 text-amber-600 ring-amber-50/50'
                        }`}>
                        {isResolve ? <CheckCircle2 className="h-3 w-3" /> :
                          isAssign ? <Briefcase className="h-3 w-3" /> : <Wrench className="h-3 w-3" />}
                      </span>
                      <div>
                        <h4 className="text-[11px] font-bold text-slate-800 leading-normal">{act.details}</h4>
                        <p className="text-[9px] text-slate-400 font-bold mt-1 tracking-wider uppercase">{act.dateTime}</p>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>

        </div>

      </div>

      {/* OVERLAY MODALS REGION */}

      {/* 1. Raise Request Modal */}
      {activeModal === 'raise' && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" onClick={() => setActiveModal(null)} />
          <div className="bg-white border border-slate-200 rounded-[2rem] max-w-lg w-full p-6 shadow-2xl space-y-4 relative z-10 animate-scale-in">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="text-sm font-black text-slate-800 flex items-center gap-2">
                <Wrench className="h-4.5 w-4.5 text-blue-600" />
                <span>Raise Support Request</span>
              </h3>
              <button onClick={() => setActiveModal(null)} className="p-1 hover:bg-slate-100 rounded-lg text-slate-400 hover:text-slate-600 transition-all">
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleRaiseSubmit} className="space-y-4">

              <div className="space-y-1">
                <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider pl-1">Select Asset / Device *</label>
                <select
                  required
                  value={repairAssetId}
                  onChange={e => setRepairAssetId(e.target.value)}
                  className="w-full p-2.5 border border-slate-200 rounded-xl text-xs focus:ring-2 focus:ring-blue-500/20 focus:outline-none font-semibold text-slate-700 bg-slate-50/50"
                >
                  <option value="">-- Choose one of your devices --</option>
                  {myAssignedAssets.map(asset => (
                    <option key={asset.id} value={asset.id}>{asset.id} - {asset.brand} {asset.model} ({asset.type})</option>
                  ))}
                </select>
              </div>

              <div className="space-y-1">
                <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider pl-1">Issue Title / Short Summary *</label>
                <input
                  type="text"
                  required
                  value={repairIssue}
                  onChange={e => setRepairIssue(e.target.value)}
                  placeholder="e.g. Keyboard keys stuck, Flickering screen"
                  className="w-full p-2.5 border border-slate-200 rounded-xl text-xs focus:ring-2 focus:ring-blue-500/20 focus:outline-none font-medium text-slate-700"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider pl-1">Priority *</label>
                  <select
                    value={repairPriority}
                    onChange={e => setRepairPriority(e.target.value)}
                    className="w-full p-2.5 border border-slate-200 rounded-xl text-xs focus:ring-2 focus:ring-blue-500/20 focus:outline-none font-semibold text-slate-700 bg-slate-50/50"
                  >
                    <option value="Low">Low</option>
                    <option value="Medium">Medium</option>
                    <option value="High">High</option>
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider pl-1">Estimated Dispatch</label>
                  <input
                    type="text"
                    disabled
                    value="Immediate Desk pickup"
                    className="w-full p-2.5 border border-slate-200 rounded-xl text-xs bg-slate-50 text-slate-400 font-semibold cursor-not-allowed"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider pl-1">Detailed Symptoms Description</label>
                <textarea
                  rows={3}
                  value={repairDesc}
                  onChange={e => setRepairDesc(e.target.value)}
                  placeholder="Provide details about the issue (e.g. error messages, when it happens, what troubleshoot steps were done)."
                  className="w-full p-2.5 border border-slate-200 rounded-xl text-xs focus:ring-2 focus:ring-blue-500/20 focus:outline-none font-medium text-slate-700"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setActiveModal(null)}
                  className="px-4 py-2 border border-slate-200 rounded-xl text-xs font-bold text-slate-500 hover:bg-slate-50 hover:text-slate-700 transition-all"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl shadow-md shadow-blue-500/10 flex items-center gap-1 transition-all"
                >
                  <Wrench className="h-4 w-4" />
                  <span>Submit Ticket</span>
                </button>
              </div>

            </form>
          </div>
        </div>
      )}

      {/* 2. Request New Asset Modal */}
      {activeModal === 'request' && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" onClick={() => setActiveModal(null)} />
          <div className="bg-white border border-slate-200 rounded-[2rem] max-w-lg w-full p-6 shadow-2xl space-y-4 relative z-10 animate-scale-in">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="text-sm font-black text-slate-800 flex items-center gap-2">
                <ShoppingBag className="h-4.5 w-4.5 text-emerald-600" />
                <span>Request New IT Asset</span>
              </h3>
              <button onClick={() => setActiveModal(null)} className="p-1 hover:bg-slate-100 rounded-lg text-slate-400 hover:text-slate-600 transition-all">
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleRequestAssetSubmit} className="space-y-4">

              <div className="space-y-1">
                <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider pl-1">Required Asset Type *</label>
                <select
                  value={newAssetType}
                  onChange={e => setNewAssetType(e.target.value)}
                  className="w-full p-2.5 border border-slate-200 rounded-xl text-xs focus:ring-2 focus:ring-blue-500/20 focus:outline-none font-semibold text-slate-700 bg-slate-50/50"
                >
                  <option value="Laptop">Laptop</option>
                  <option value="Monitor">Monitor</option>
                  <option value="Keyboard">Keyboard</option>
                  <option value="Mouse">Mouse</option>
                  <option value="Headset">Headset</option>
                  <option value="Docking Station">Docking Station</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider pl-1">Priority *</label>
                  <select
                    value={newAssetPriority}
                    onChange={e => setNewAssetPriority(e.target.value)}
                    className="w-full p-2.5 border border-slate-200 rounded-xl text-xs focus:ring-2 focus:ring-blue-500/20 focus:outline-none font-semibold text-slate-700 bg-slate-50/50"
                  >
                    <option value="Low">Low (General Upgrade)</option>
                    <option value="Medium">Medium (Operational Need)</option>
                    <option value="High">High (Immediate Replacement)</option>
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider pl-1">Requester Department</label>
                  <input
                    type="text"
                    disabled
                    value={currentUser.department}
                    className="w-full p-2.5 border border-slate-200 rounded-xl text-xs bg-slate-50 text-slate-400 font-semibold cursor-not-allowed"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider pl-1">Justification Reason & Requirements *</label>
                <textarea
                  rows={3}
                  required
                  value={newAssetReason}
                  onChange={e => setNewAssetReason(e.target.value)}
                  placeholder="State the business reasoning for requesting this device (e.g. dual monitor support, keyboard keys broken, hardware upgrade eligibility, joining project requirements)."
                  className="w-full p-2.5 border border-slate-200 rounded-xl text-xs focus:ring-2 focus:ring-blue-500/20 focus:outline-none font-medium text-slate-700"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setActiveModal(null)}
                  className="px-4 py-2 border border-slate-200 rounded-xl text-xs font-bold text-slate-500 hover:bg-slate-50 hover:text-slate-700 transition-all"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl shadow-md shadow-emerald-500/10 flex items-center gap-1.5 transition-all"
                >
                  <ShoppingBag className="h-4 w-4" />
                  <span>Submit Request</span>
                </button>
              </div>

            </form>
          </div>
        </div>
      )}

      {/* 3. Check Request Status & History timelines Modal */}
      {activeModal === 'status' && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" onClick={() => setActiveModal(null)} />
          <div className="bg-white border border-slate-200 rounded-[2rem] max-w-4xl w-full p-6 shadow-2xl flex flex-col md:flex-row gap-6 relative z-10 animate-scale-in max-h-[85vh] overflow-y-auto">

            {/* Left Hand: Ticket Listing */}
            <div className="md:w-5/12 border-r border-slate-100 pr-0 md:pr-6 space-y-4">
              <h3 className="text-sm font-black text-slate-800 flex items-center gap-2">
                <ClipboardList className="h-5 w-5 text-purple-600" />
                <span>My Requests Directory</span>
              </h3>

              <div className="space-y-2.5 overflow-y-auto max-h-[50vh] pr-1">
                {sortedRepairs.length === 0 ? (
                  <p className="text-xs text-slate-400 py-6 text-center">No tickets found.</p>
                ) : (
                  sortedRepairs.map(rep => (
                    <div
                      key={rep.id}
                      onClick={() => setSelectedRepairId(rep.id)}
                      className={`p-3 border rounded-2xl cursor-pointer text-left transition-all ${selectedRepairId === rep.id
                          ? 'bg-purple-50/50 border-purple-400'
                          : 'border-slate-150 hover:bg-slate-50/40 bg-slate-50/20'
                        }`}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">{rep.id}</span>
                        <span className={`px-2 py-0.5 rounded-full text-[8px] font-extrabold uppercase ${rep.status === 'Resolved' || rep.status === 'Completed' ? 'bg-emerald-50 text-emerald-600' :
                            rep.status === 'In Progress' ? 'bg-amber-50 text-amber-600' :
                              rep.status === 'Cancelled' ? 'bg-slate-100 text-slate-500' : 'bg-blue-50 text-blue-600'
                          }`}>{rep.status}</span>
                      </div>
                      <h4 className="text-xs font-bold text-slate-800 mt-1 truncate">{rep.issue}</h4>
                      <p className="text-[9px] text-slate-400 font-bold mt-1">{rep.requestDate.split(' ')[0]}</p>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Right Hand: Ticket Details & History Timeline */}
            <div className="flex-1 space-y-4 flex flex-col justify-between">
              <div>
                <div className="flex justify-between items-start">
                  <h4 className="text-sm font-black text-slate-800">Support Ticket Log</h4>
                  <button onClick={() => setActiveModal(null)} className="p-1 hover:bg-slate-100 rounded-lg text-slate-400 hover:text-slate-600 transition-all md:hidden">
                    <X className="h-5 w-5" />
                  </button>
                </div>

                {selectedRepairDetails ? (
                  <div className="space-y-4 mt-2">
                    <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100 space-y-2.5">
                      <div className="flex flex-wrap gap-2 text-[10px] font-bold text-slate-400 uppercase">
                        <span>Ticket ID: {selectedRepairDetails.id}</span>
                        <span>&bull;</span>
                        <span>Device: {selectedRepairDetails.assetId}</span>
                        <span>&bull;</span>
                        <span>Priority: {selectedRepairDetails.priority}</span>
                      </div>
                      <h3 className="text-xs font-bold text-slate-800">{selectedRepairDetails.issue}</h3>
                      <p className="text-[10px] text-slate-400 font-medium leading-relaxed">{selectedRepairDetails.description}</p>
                    </div>

                    {/* Visual Progress Stepper Bar */}
                    <div className="p-4 bg-slate-50/80 rounded-2xl border border-slate-200/80 space-y-3">
                      <p className="text-[10px] font-extrabold text-slate-400 uppercase tracking-wider">Ticket Progress Tracker</p>

                      <div className="flex items-center justify-between relative px-2">
                        {/* Step 1: Raised */}
                        <div className="flex flex-col items-center gap-1 z-10">
                          <div className="h-7 w-7 rounded-full bg-blue-600 text-white flex items-center justify-center text-[10px] font-bold shadow-xs">
                            1
                          </div>
                          <span className="text-[9px] font-bold text-slate-700">Raised</span>
                        </div>

                        {/* Step 2: Accepted */}
                        <div className="flex flex-col items-center gap-1 z-10">
                          <div className={`h-7 w-7 rounded-full flex items-center justify-center text-[10px] font-bold transition-all ${selectedRepairDetails.acceptedBy
                              ? 'bg-emerald-600 text-white shadow-xs'
                              : 'bg-slate-200 text-slate-400'
                            }`}>
                            2
                          </div>
                          <span className={`text-[9px] font-bold ${selectedRepairDetails.acceptedBy ? 'text-emerald-700' : 'text-slate-400'}`}>
                            {selectedRepairDetails.acceptedBy ? 'Accepted' : 'Pending Admin'}
                          </span>
                        </div>

                        {/* Step 3: In Progress */}
                        <div className="flex flex-col items-center gap-1 z-10">
                          <div className={`h-7 w-7 rounded-full flex items-center justify-center text-[10px] font-bold transition-all ${selectedRepairDetails.status === 'In Progress' || selectedRepairDetails.status === 'Awaiting Parts' || selectedRepairDetails.status === 'Completed' || selectedRepairDetails.status === 'Resolved'
                              ? 'bg-blue-600 text-white shadow-xs'
                              : 'bg-slate-200 text-slate-400'
                            }`}>
                            3
                          </div>
                          <span className={`text-[9px] font-bold ${selectedRepairDetails.status === 'In Progress' || selectedRepairDetails.status === 'Awaiting Parts' ? 'text-blue-700' : 'text-slate-400'}`}>
                            {selectedRepairDetails.status === 'Awaiting Parts' ? 'Awaiting Parts' : 'In Progress'}
                          </span>
                        </div>

                        {/* Step 4: Resolved */}
                        <div className="flex flex-col items-center gap-1 z-10">
                          <div className={`h-7 w-7 rounded-full flex items-center justify-center text-[10px] font-bold transition-all ${selectedRepairDetails.status === 'Completed' || selectedRepairDetails.status === 'Resolved'
                              ? 'bg-emerald-600 text-white shadow-xs'
                              : 'bg-slate-200 text-slate-400'
                            }`}>
                            4
                          </div>
                          <span className={`text-[9px] font-bold ${selectedRepairDetails.status === 'Completed' || selectedRepairDetails.status === 'Resolved' ? 'text-emerald-700' : 'text-slate-400'}`}>
                            Resolved
                          </span>
                        </div>
                      </div>

                      {selectedRepairDetails.acceptedBy && (
                        <div className="mt-2 pt-2 border-t border-slate-200/60 flex items-center justify-between text-[10px]">
                          <span className="text-slate-400 font-medium">Assigned IT Admin:</span>
                          <span className="font-extrabold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200/60">
                            ✓ {selectedRepairDetails.acceptedBy}
                          </span>
                        </div>
                      )}
                    </div>

                    <div className="space-y-3">
                      <h5 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest pl-1">Progress History Logs</h5>
                      <div className="relative pl-6 space-y-4 border-l border-slate-100 ml-3">
                        {selectedRepairDetails.updates.map((update, idx) => (
                          <div key={idx} className="relative">
                            <span className="absolute -left-[33px] top-0.5 p-1 bg-purple-50 text-purple-600 border border-purple-200 rounded-full shrink-0 ring-4 ring-white">
                              <Clock className="h-2.5 w-2.5" />
                            </span>
                            <div>
                              <p className="text-xs font-semibold text-slate-700">{update.message}</p>
                              <p className="text-[9px] text-slate-400 font-bold mt-0.5">{update.date}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="py-20 text-center text-slate-400 space-y-2.5">
                    <HelpCircle className="h-10 w-10 text-slate-300 mx-auto" />
                    <p className="text-xs">Select a request ticket to inspect status details and tracking log logs.</p>
                  </div>
                )}
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setActiveModal(null)}
                  className="px-4 py-2 border border-slate-200 rounded-xl text-xs font-bold text-slate-500 hover:bg-slate-50 hover:text-slate-700 transition-all w-full md:w-auto"
                >
                  Close Directory
                </button>
              </div>
            </div>

          </div>
        </div>
      )}

      {/* 4. IT Guidelines Modal */}
      {activeModal === 'guidelines' && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" onClick={() => setActiveModal(null)} />
          <div className="bg-white border border-slate-200 rounded-[2rem] max-w-xl w-full p-6 shadow-2xl space-y-4 relative z-10 animate-scale-in max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="text-sm font-black text-slate-800 flex items-center gap-2">
                <BookOpen className="h-4.5 w-4.5 text-amber-500" />
                <span>IT Asset Usage Guidelines</span>
              </h3>
              <button onClick={() => setActiveModal(null)} className="p-1 hover:bg-slate-100 rounded-lg text-slate-400 hover:text-slate-600 transition-all">
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4 text-xs text-slate-600 leading-relaxed max-h-[50vh] overflow-y-auto pr-1">

              {/* Official Admin PDF Banner */}
              <div className="bg-slate-50 border border-slate-200/80 rounded-2xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex items-start gap-3 min-w-0">
                  <div className="p-3 bg-red-50 text-red-600 rounded-xl border border-red-100 shrink-0">
                    <FileText className="h-6 w-6" />
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h4 className="font-extrabold text-slate-800 text-xs truncate">{guidelines?.title || 'Quadrant IT Asset Usage Guidelines 2026'}</h4>
                      <span className="px-2 py-0.5 text-[9px] font-extrabold bg-blue-50 text-blue-700 rounded-md border border-blue-100 shrink-0">
                        {guidelines?.version || 'v2.4'}
                      </span>
                    </div>
                    <p className="text-[10px] text-slate-500 mt-1">{guidelines?.summary}</p>
                    <div className="flex items-center gap-3 text-[10px] text-slate-400 font-semibold mt-2">
                      <span>File: <strong className="text-slate-700">{guidelines?.fileName || 'Quadrant_IT_Asset_Policy_2026.pdf'}</strong></span>
                      <span>Date: {guidelines?.uploadedDate}</span>
                    </div>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    showToast(`Opening & Downloading ${guidelines?.fileName || 'Asset_Guidelines.pdf'}...`, 'info');
                    downloadOrOpenGuidelinesPdf(guidelines);
                  }}
                  className="flex items-center justify-center gap-1.5 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl shadow-md shadow-blue-500/10 transition-all shrink-0 cursor-pointer"
                >
                  <Download className="h-3.5 w-3.5" />
                  <span>Download / Open PDF</span>
                </button>
              </div>

              <div className="space-y-2">
                <h4 className="font-bold text-slate-800 text-xs flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 bg-blue-600 rounded-full"></span>
                  <span>1. Safe Handling & Maintenance</span>
                </h4>
                <p className="pl-3.5 text-slate-400">All assets assigned to employees are properties of the company. Please keep laptops clean, avoid liquids in vicinity, and shut down devices periodically to ensure cooling system efficiency.</p>
              </div>

              <div className="space-y-2">
                <h4 className="font-bold text-slate-800 text-xs flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 bg-blue-600 rounded-full"></span>
                  <span>2. Software Installation & Compliance</span>
                </h4>
                <p className="pl-3.5 text-slate-400">Only authorized corporate licensing applications should be downloaded. Do not install unauthorized VPNs, peer-to-peer torrent handlers, or cracked games. Periodic audits are run by system security engineers.</p>
              </div>

              <div className="space-y-2">
                <h4 className="font-bold text-slate-800 text-xs flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 bg-blue-600 rounded-full"></span>
                  <span>3. Reporting Theft or Physical Damage</span>
                </h4>
                <p className="pl-3.5 text-slate-400">In the case of physical breakage, accidental liquid damage, or hardware thefts, raise a High priority ticket immediately. For thefts, coordinate with local safety departments and report with police FIR details.</p>
              </div>

              <div className="space-y-2">
                <h4 className="font-bold text-slate-800 text-xs flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 bg-blue-600 rounded-full"></span>
                  <span>4. Asset Return Policy</span>
                </h4>
                <p className="pl-3.5 text-slate-400">Upon employee resignation or offboarding processes, all assigned materials (laptops, monitors, chargers, keys) must be returned directly to the central IT desk within 48 hours for inventory clearance checkoffs.</p>
              </div>

            </div>

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setActiveModal(null)}
                className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white font-bold text-xs rounded-xl shadow-md shadow-amber-500/10 transition-all w-full sm:w-auto"
              >
                I Understand
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 5. View All Assigned Assets Modal */}
      {activeModal === 'all_assets' && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" onClick={() => setActiveModal(null)} />
          <div className="bg-white border border-slate-200 rounded-[2rem] max-w-3xl w-full p-6 shadow-2xl space-y-4 relative z-10 animate-scale-in max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="text-sm font-black text-slate-800 flex items-center gap-2">
                <Briefcase className="h-4.5 w-4.5 text-blue-600" />
                <span>My Assigned Equipment ({totalAssignedCount})</span>
              </h3>
              <button onClick={() => setActiveModal(null)} className="p-1 hover:bg-slate-100 rounded-lg text-slate-400 hover:text-slate-600 transition-all">
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="overflow-x-auto max-h-[50vh] pr-1">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-slate-100 text-[9px] font-bold text-slate-400 uppercase tracking-wider">
                    <th className="pb-3 pr-3">Asset ID</th>
                    <th className="pb-3 px-3">Device details</th>
                    <th className="pb-3 px-3">Serial Number</th>
                    <th className="pb-3 px-3">Assign Date</th>
                    <th className="pb-3 px-3">Status</th>
                    <th className="pb-3 pl-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50 text-slate-700">
                  {myAssignedAssets.map(asset => (
                    <tr key={asset.id} className="hover:bg-slate-50/30 transition-all">
                      <td className="py-3.5 pr-3 font-bold text-blue-600">{asset.id}</td>
                      <td className="py-3.5 px-3">
                        <div className="flex items-center gap-2.5">
                          <AssetIconBadge type={asset.type} className="h-7 w-7 rounded-lg shrink-0" iconSize="h-3.5 w-3.5" />
                          <div>
                            <p className="font-bold text-slate-800">{asset.brand} {asset.model}</p>
                            <p className="text-[9px] text-slate-400 font-semibold">{asset.type}</p>
                          </div>
                        </div>
                      </td>
                      <td className="py-3.5 px-3 font-medium text-slate-600">{asset.serialNumber}</td>
                      <td className="py-3.5 px-3 text-slate-500 font-semibold">{asset.purchaseDate || '10 May 2024'}</td>
                      <td className="py-3.5 px-3">
                        <span className={`px-2.5 py-0.5 rounded-lg text-[9px] font-extrabold uppercase border ${asset.status === 'Assigned' ? 'bg-blue-50 text-[#1E3A8A] border-blue-200/60' : 'bg-rose-50 text-rose-600 border-rose-200/60'
                          }`}>
                          {asset.status === 'Assigned' ? 'Active' : 'Under Repair'}
                        </span>
                      </td>
                      <td className="py-3.5 pl-3 text-right">
                        <button
                          onClick={() => {
                            setRepairAssetId(asset.id);
                            setRepairIssue(`Issue with ${asset.brand} ${asset.model}`);
                            setActiveModal('raise');
                          }}
                          className="px-2 py-1 bg-blue-50 hover:bg-blue-100 text-blue-600 rounded-lg text-[10px] font-bold transition-all"
                        >
                          Report Fault
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setActiveModal(null)}
                className="px-4 py-2 border border-slate-200 rounded-xl text-xs font-bold text-slate-500 hover:bg-slate-50 hover:text-slate-700 transition-all w-full sm:w-auto"
              >
                Close Inventory
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 6. All Recent Announcements Modal */}
      {activeModal === 'announcements' && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" onClick={() => setActiveModal(null)} />
          <div className="bg-white border border-slate-200 rounded-[2rem] max-w-2xl w-full p-6 shadow-2xl space-y-4 relative z-10 animate-scale-in max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="text-sm font-black text-slate-800 flex items-center gap-2">
                <Info className="h-4.5 w-4.5 text-blue-600" />
                <span>Company Broadcast Announcements ({(announcements || []).length})</span>
              </h3>
              <button onClick={() => setActiveModal(null)} className="p-1 hover:bg-slate-100 rounded-lg text-slate-400 hover:text-slate-600 transition-all">
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-3 max-h-[55vh] overflow-y-auto pr-1">
              {(!announcements || announcements.length === 0) ? (
                <p className="text-xs text-slate-400 font-semibold py-6 text-center">No announcements broadcasted yet.</p>
              ) : (
                announcements.map((ann) => (
                  <div key={ann.id} className="p-4 bg-slate-50 rounded-2xl border border-slate-200/80 space-y-2">
                    <div className="flex items-center justify-between gap-2 flex-wrap">
                      <h4 className="font-extrabold text-slate-800 text-xs">{ann.title}</h4>
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-0.5 text-[9px] font-extrabold rounded-md border ${ann.priority === 'High' || ann.priority === 'Urgent' ? 'bg-red-50 text-red-600 border-red-200' : 'bg-blue-50 text-blue-600 border-blue-200'
                          }`}>
                          {ann.type || 'General'}
                        </span>
                        <span className="text-[10px] text-slate-400 font-bold">{ann.date}</span>
                      </div>
                    </div>
                    <p className="text-xs text-slate-600 leading-relaxed">{ann.message}</p>
                    <p className="text-[10px] text-slate-400 font-semibold pt-1 border-t border-slate-200/50">
                      Author: {ann.author}
                    </p>
                  </div>
                ))
              )}
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setActiveModal(null)}
                className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold shadow-md shadow-blue-500/10 transition-all"
              >
                Close Announcements
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};

export default EmployeeDashboard;
