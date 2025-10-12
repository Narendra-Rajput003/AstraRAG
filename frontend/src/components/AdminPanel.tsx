'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Users,
  FileText,
  Mail,
  Plus,
  Trash2,
  Check,
  X,
  Shield
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { adminAPI } from '@/services/api';
import { AdminInvite, AdminDocument, AdminUser } from '@/types';
import { useToastContext } from '@/contexts/ToastContext';
import { useWebSocket } from '@/contexts/WebSocketContext';
import { SkeletonList } from '@/components/LoadingSkeleton';

interface AdminPanelProps {
  className?: string;
}

type TabType = 'invites' | 'documents' | 'users';

export const AdminPanel: React.FC<AdminPanelProps> = ({ className = '' }) => {
  const { user } = useAuth();
  const { success, error: toastError } = useToastContext();
  const { socket, isConnected } = useWebSocket();
  const [activeTab, setActiveTab] = useState<TabType>('invites');
  const [loading, setLoading] = useState(false);

  // Invites state
  const [invites, setInvites] = useState<AdminInvite[]>([]);
  const [newInviteEmail, setNewInviteEmail] = useState('');
  const [newInviteRole, setNewInviteRole] = useState('employee');

  // Documents state
  const [pendingDocuments, setPendingDocuments] = useState<AdminDocument[]>([]);

  // Users state
  const [users, setUsers] = useState<AdminUser[]>([]);

  const isAdmin = user?.role?.startsWith('admin') || user?.role === 'superadmin';

  useEffect(() => {
    if (isAdmin) {
      loadTabData(activeTab);
    }
  }, [activeTab, isAdmin]);

  // WebSocket event listeners for real-time updates
  useEffect(() => {
    if (!socket || !isAdmin) return;

    const handleDocumentUploaded = (data: { filename: string }) => {
      if (activeTab === 'documents') {
        loadTabData('documents'); // Refresh pending documents
      }
      success(`New document uploaded: ${data.filename}`);
    };

    const handleDocumentApproved = (data: { filename: string }) => {
      if (activeTab === 'documents') {
        loadTabData('documents'); // Refresh pending documents
      }
      success(`Document approved: ${data.filename}`);
    };

    socket.on('document_uploaded', handleDocumentUploaded);
    socket.on('document_approved', handleDocumentApproved);

    return () => {
      socket.off('document_uploaded', handleDocumentUploaded);
      socket.off('document_approved', handleDocumentApproved);
    };
  }, [socket, isAdmin, activeTab, success]);

  const loadTabData = async (tab: TabType) => {
    setLoading(true);
    try {
      switch (tab) {
        case 'invites':
          const invitesData = await adminAPI.listInvites();
          setInvites(invitesData);
          break;
        case 'documents':
          const docsData = await adminAPI.getPendingDocuments();
          setPendingDocuments(docsData);
          break;
        case 'users':
          const usersData = await adminAPI.getUsers();
          setUsers(usersData);
          break;
      }
    } catch (err) {
      toastError(`Failed to load ${tab} data`);
      console.error(`Error loading ${tab}:`, err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateInvite = async () => {
    if (!newInviteEmail.trim()) return;

    try {
      await adminAPI.createInvite(newInviteEmail, newInviteRole);
      setNewInviteEmail('');
      setNewInviteRole('employee');
      loadTabData('invites');
      success('Invite created successfully');
    } catch (err) {
      toastError('Failed to create invite');
      console.error('Error creating invite:', err);
    }
  };

  const handleRevokeInvite = async (inviteId: string) => {
    try {
      await adminAPI.revokeInvite(inviteId);
      loadTabData('invites');
      success('Invite revoked successfully');
    } catch (err) {
      toastError('Failed to revoke invite');
      console.error('Error revoking invite:', err);
    }
  };

  const handleDocumentAction = async (docId: string, action: 'approve' | 'reject') => {
    try {
      await adminAPI.approveDocument(docId, action);
      loadTabData('documents');
      success(`Document ${action}d successfully`);
    } catch (err) {
      toastError(`Failed to ${action} document`);
      console.error(`Error ${action}ing document:`, err);
    }
  };

  if (!isAdmin) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-800 rounded-lg">
        <div className="text-center">
          <Shield className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-white mb-2">Access Denied</h3>
          <p className="text-gray-400">You need admin privileges to access this panel.</p>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: 'invites' as TabType, label: 'Invites', icon: Mail, count: invites.length },
    { id: 'documents' as TabType, label: 'Documents', icon: FileText, count: pendingDocuments.length },
    { id: 'users' as TabType, label: 'Users', icon: Users, count: users.length },
  ];

  return (
    <div className={`bg-gray-800 rounded-lg overflow-hidden ${className}`}>
      {/* Header */}
      <div className="bg-gray-900 px-6 py-4 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-white flex items-center gap-2">
              <Shield className="h-5 w-5 text-blue-500" />
              Admin Panel
            </h2>
            <p className="text-gray-400 text-sm mt-1">Manage users, documents, and system settings</p>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className={isConnected ? 'text-green-400' : 'text-red-400'}>
              {isConnected ? 'Live' : 'Offline'}
            </span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-700">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-6 py-3 text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? 'text-blue-500 border-b-2 border-blue-500 bg-gray-800'
                : 'text-gray-400 hover:text-white hover:bg-gray-700'
            }`}
          >
            <tab.icon className="h-4 w-4" />
            {tab.label}
            {tab.count > 0 && (
              <span className="bg-blue-500 text-white text-xs px-2 py-1 rounded-full">
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="p-6">

        <AnimatePresence mode="wait">
          {loading ? (
            <motion.div
              key="loading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <SkeletonList count={3} />
            </motion.div>
          ) : (
            <>
              {/* Invites Tab */}
              {activeTab === 'invites' && (
                <motion.div
                  key="invites"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                >
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold text-white mb-4">Create New Invite</h3>
                    <div className="flex gap-3">
                      <input
                        type="email"
                        placeholder="Email address"
                        value={newInviteEmail}
                        onChange={(e) => setNewInviteEmail(e.target.value)}
                        className="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      <select
                        value={newInviteRole}
                        onChange={(e) => setNewInviteRole(e.target.value)}
                        className="bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="employee">Employee</option>
                        <option value="admin:hr">Admin HR</option>
                        <option value="superadmin">Super Admin</option>
                      </select>
                      <motion.button
                        onClick={handleCreateInvite}
                        disabled={!newInviteEmail.trim()}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed flex items-center gap-2"
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                      >
                        <Plus className="h-4 w-4" />
                        Create
                      </motion.button>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-lg font-semibold text-white mb-4">Existing Invites</h3>
                    <div className="space-y-3">
                      {invites.map((invite) => (
                        <div key={invite.id} className="bg-gray-700 rounded-lg p-4">
                          <div className="flex items-center justify-between">
                            <div>
                              <div className="text-white font-medium">{invite.email}</div>
                              <div className="text-gray-400 text-sm">
                                Role: {invite.role} • Created: {new Date(invite.created_at || '').toLocaleDateString()}
                              </div>
                              {invite.used && (
                                <div className="text-green-400 text-sm">Used by: {invite.used_by}</div>
                              )}
                            </div>
                            {!invite.used && (
                              <motion.button
                                onClick={() => handleRevokeInvite(invite.id)}
                                className="p-2 text-red-400 hover:text-red-300 hover:bg-red-900/20 rounded-lg"
                                whileHover={{ scale: 1.1 }}
                                whileTap={{ scale: 0.9 }}
                              >
                                <Trash2 className="h-4 w-4" />
                              </motion.button>
                            )}
                          </div>
                        </div>
                      ))}
                      {invites.length === 0 && (
                        <div className="text-center text-gray-400 py-8">No invites found</div>
                      )}
                    </div>
                  </div>
                </motion.div>
              )}

              {/* Documents Tab */}
              {activeTab === 'documents' && (
                <motion.div
                  key="documents"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                >
                  <h3 className="text-lg font-semibold text-white mb-4">Pending Document Approvals</h3>
                  <div className="space-y-3">
                    {pendingDocuments.map((doc) => (
                      <div key={doc.doc_id} className="bg-gray-700 rounded-lg p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="text-white font-medium">{doc.filename}</div>
                            <div className="text-gray-400 text-sm">
                              Uploaded: {new Date(doc.uploaded_at || '').toLocaleDateString()} •
                              By: {doc.uploaded_by}
                            </div>
                            {doc.metadata && typeof doc.metadata === 'object' && 'file_size' in doc.metadata && typeof doc.metadata.file_size === 'number' && (
                              <div className="text-gray-500 text-xs">
                                Size: {(doc.metadata.file_size / 1024 / 1024).toFixed(2)} MB
                              </div>
                            )}
                          </div>
                          <div className="flex gap-2">
                            <motion.button
                              onClick={() => handleDocumentAction(doc.doc_id, 'approve')}
                              className="p-2 text-green-400 hover:text-green-300 hover:bg-green-900/20 rounded-lg"
                              whileHover={{ scale: 1.1 }}
                              whileTap={{ scale: 0.9 }}
                            >
                              <Check className="h-4 w-4" />
                            </motion.button>
                            <motion.button
                              onClick={() => handleDocumentAction(doc.doc_id, 'reject')}
                              className="p-2 text-red-400 hover:text-red-300 hover:bg-red-900/20 rounded-lg"
                              whileHover={{ scale: 1.1 }}
                              whileTap={{ scale: 0.9 }}
                            >
                              <X className="h-4 w-4" />
                            </motion.button>
                          </div>
                        </div>
                      </div>
                    ))}
                    {pendingDocuments.length === 0 && (
                      <div className="text-center text-gray-400 py-8">No pending documents</div>
                    )}
                  </div>
                </motion.div>
              )}

              {/* Users Tab */}
              {activeTab === 'users' && (
                <motion.div
                  key="users"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                >
                  <h3 className="text-lg font-semibold text-white mb-4">System Users</h3>
                  <div className="space-y-3">
                    {users.map((user) => (
                      <div key={user.user_id} className="bg-gray-700 rounded-lg p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="text-white font-medium">{user.email}</div>
                            <div className="text-gray-400 text-sm">Role: {user.role}</div>
                          </div>
                          <div className={`px-2 py-1 rounded-full text-xs ${
                            user.is_active
                              ? 'bg-green-900/20 text-green-400'
                              : 'bg-red-900/20 text-red-400'
                          }`}>
                            {user.is_active ? 'Active' : 'Inactive'}
                          </div>
                        </div>
                      </div>
                    ))}
                    {users.length === 0 && (
                      <div className="text-center text-gray-400 py-8">No users found</div>
                    )}
                  </div>
                </motion.div>
              )}
            </>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default AdminPanel;