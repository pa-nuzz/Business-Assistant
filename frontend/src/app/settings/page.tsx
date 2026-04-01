'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { profile, auth, user } from '@/lib/api';
import { 
  User, Building2, Save, Loader2, ArrowLeft, LogOut, 
  Camera, Lock, UserCircle 
} from 'lucide-react';

interface UserProfile {
  username?: string;
  first_name?: string;
  last_name?: string;
  email?: string;
  company_name?: string;
  industry?: string;
  company_size?: string;
  avatar?: string;
}

export default function SettingsPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [loading, setLoading] = useState(true);
  const [savingProfile, setSavingProfile] = useState(false);
  const [savingUsername, setSavingUsername] = useState(false);
  const [savingPassword, setSavingPassword] = useState(false);
  const [uploadingAvatar, setUploadingAvatar] = useState(false);
  
  const [activeTab, setActiveTab] = useState<'profile' | 'business' | 'security'>('profile');
  
  const [profileData, setProfileData] = useState<UserProfile>({});
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  
  const [newUsername, setNewUsername] = useState('');
  
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const [profileRes, userRes] = await Promise.all([
        profile.get().catch(() => ({})),
        user.getInfo().catch(() => ({})),
      ]);
      
      const combined = {
        ...profileRes,
        ...userRes,
        company_name: profileRes.company_name || '',
        industry: profileRes.industry || '',
        company_size: profileRes.company_size || '',
      };
      
      setProfileData(combined);
      setNewUsername(userRes.username || '');
      if (userRes.avatar) {
        setAvatarPreview(userRes.avatar);
      }
    } catch (err) {
      toast.error('Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  const handleAvatarClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      toast.error('Please select an image file');
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      toast.error('Image must be less than 5MB');
      return;
    }

    setSelectedFile(file);
    const reader = new FileReader();
    reader.onloadend = () => {
      setAvatarPreview(reader.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleAvatarUpload = async () => {
    if (!selectedFile) return;

    setUploadingAvatar(true);
    try {
      await profile.updateWithAvatar({}, selectedFile);
      toast.success('Profile picture updated successfully');
      setSelectedFile(null);
      router.refresh();
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'Failed to upload avatar');
    } finally {
      setUploadingAvatar(false);
    }
  };

  const handleUsernameUpdate = async () => {
    if (!newUsername.trim() || newUsername === profileData.username) {
      toast.error('Please enter a different username');
      return;
    }

    setSavingUsername(true);
    try {
      await user.updateUsername(newUsername.trim());
      setProfileData(prev => ({ ...prev, username: newUsername.trim() }));
      toast.success('Username updated successfully');
      router.refresh();
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'Failed to update username');
    } finally {
      setSavingUsername(false);
    }
  };

  const handlePasswordUpdate = async () => {
    const { currentPassword, newPassword, confirmPassword } = passwordData;

    if (!currentPassword || !newPassword || !confirmPassword) {
      toast.error('All password fields are required');
      return;
    }

    if (newPassword.length < 8) {
      toast.error('New password must be at least 8 characters');
      return;
    }

    if (newPassword !== confirmPassword) {
      toast.error('New passwords do not match');
      return;
    }

    setSavingPassword(true);
    try {
      await user.updatePassword(currentPassword, newPassword);
      setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' });
      toast.success('Password updated successfully. Please log in again with your new password.');
      setTimeout(() => {
        auth.logout();
        router.push('/login');
      }, 2000);
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'Failed to update password');
    } finally {
      setSavingPassword(false);
    }
  };

  const handleSaveProfile = async () => {
    setSavingProfile(true);
    try {
      await profile.update({
        company_name: profileData.company_name,
        industry: profileData.industry,
        company_size: profileData.company_size,
      });
      toast.success('Business profile saved successfully');
      router.refresh();
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'Failed to save profile');
    } finally {
      setSavingProfile(false);
    }
  };

  const handleLogout = () => {
    auth.logout();
    router.push('/login');
    toast.success('Logged out successfully');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="mb-8">
        <button
          onClick={() => router.push('/chat')}
          className="flex items-center gap-2 text-sm text-gray-600 hover:text-black transition-colors mb-4"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Chat
        </button>
        <h1 className="text-2xl font-semibold text-gray-900">Settings</h1>
        <p className="mt-1 text-sm text-gray-600">Manage your profile, account, and preferences</p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex gap-8">
          <button
            onClick={() => setActiveTab('profile')}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-all ${
              activeTab === 'profile'
                ? 'border-black text-black'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <span className="flex items-center gap-2">
              <UserCircle className="h-4 w-4" />
              Profile
            </span>
          </button>
          <button
            onClick={() => setActiveTab('business')}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-all ${
              activeTab === 'business'
                ? 'border-black text-black'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <span className="flex items-center gap-2">
              <Building2 className="h-4 w-4" />
              Business
            </span>
          </button>
          <button
            onClick={() => setActiveTab('security')}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-all ${
              activeTab === 'security'
                ? 'border-black text-black'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <span className="flex items-center gap-2">
              <Lock className="h-4 w-4" />
              Security
            </span>
          </button>
        </nav>
      </div>

      {/* Profile Tab */}
      {activeTab === 'profile' && (
        <div className="space-y-6">
          {/* Avatar Section */}
          <div className="bg-white shadow-sm border border-gray-200 rounded-xl p-6 hover:shadow-md transition-shadow">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Profile Picture</h3>
            <div className="flex items-center gap-6">
              <div className="relative group">
                <div 
                  onClick={handleAvatarClick}
                  className="w-24 h-24 rounded-full bg-gray-200 flex items-center justify-center cursor-pointer overflow-hidden hover:ring-4 hover:ring-gray-100 transition-all group-hover:scale-105"
                >
                  {avatarPreview ? (
                    <img 
                      src={avatarPreview} 
                      alt="Profile" 
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <User className="h-12 w-12 text-gray-400" />
                  )}
                </div>
                <button
                  onClick={handleAvatarClick}
                  className="absolute bottom-0 right-0 bg-black text-white p-2 rounded-full hover:bg-gray-800 transition-all hover:scale-110"
                >
                  <Camera className="h-4 w-4" />
                </button>
              </div>
              <div className="flex-1">
                <p className="text-sm text-gray-600 mb-2">
                  Click to upload a new profile picture
                </p>
                <p className="text-xs text-gray-500">
                  Recommended: Square image, at least 200x200px, max 5MB
                </p>
                {selectedFile && (
                  <div className="mt-3 flex items-center gap-3">
                    <button
                      onClick={handleAvatarUpload}
                      disabled={uploadingAvatar}
                      className="flex items-center gap-2 px-4 py-2 bg-black text-white text-sm rounded-lg hover:bg-gray-800 disabled:opacity-50 transition-all hover:scale-105 active:scale-95"
                    >
                      {uploadingAvatar ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Camera className="h-4 w-4" />
                      )}
                      {uploadingAvatar ? 'Uploading...' : 'Save Photo'}
                    </button>
                    <button
                      onClick={() => {
                        setSelectedFile(null);
                        setAvatarPreview(profileData.avatar || null);
                      }}
                      className="px-4 py-2 text-gray-600 text-sm hover:text-gray-900 transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                )}
              </div>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleFileChange}
              className="hidden"
            />
          </div>

          {/* Username Section */}
          <div className="bg-white shadow-sm border border-gray-200 rounded-xl p-6 hover:shadow-md transition-shadow">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Username</h3>
            <div className="flex gap-4">
              <div className="flex-1">
                <input
                  type="text"
                  value={newUsername}
                  onChange={(e) => setNewUsername(e.target.value)}
                  className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-black focus:outline-none focus:ring-1 focus:ring-black transition-all"
                  placeholder="Enter username"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Your username must be at least 3 characters
                </p>
              </div>
              <button
                onClick={handleUsernameUpdate}
                disabled={savingUsername}
                className="flex items-center gap-2 px-6 py-2 bg-black text-white text-sm rounded-lg hover:bg-gray-800 disabled:opacity-50 transition-all hover:scale-105 active:scale-95"
              >
                {savingUsername ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Save className="h-4 w-4" />
                )}
                {savingUsername ? 'Saving...' : 'Update'}
              </button>
            </div>
          </div>

          {/* Logout Section */}
          <div className="bg-white shadow-sm border border-gray-200 rounded-xl p-6 hover:shadow-md transition-shadow">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Session</h3>
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 text-red-600 hover:text-red-700 text-sm font-medium transition-colors hover:scale-105"
            >
              <LogOut className="h-4 w-4" />
              Sign out
            </button>
          </div>
        </div>
      )}

      {/* Security Tab */}
      {activeTab === 'security' && (
        <div className="bg-white shadow-sm border border-gray-200 rounded-xl p-6 hover:shadow-md transition-shadow">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Change Password</h3>
          <div className="space-y-4 max-w-md">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Current Password
              </label>
              <input
                type="password"
                value={passwordData.currentPassword}
                onChange={(e) => setPasswordData(prev => ({ ...prev, currentPassword: e.target.value }))}
                className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-black focus:outline-none focus:ring-1 focus:ring-black transition-all"
                placeholder="Enter current password"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                New Password
              </label>
              <input
                type="password"
                value={passwordData.newPassword}
                onChange={(e) => setPasswordData(prev => ({ ...prev, newPassword: e.target.value }))}
                className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-black focus:outline-none focus:ring-1 focus:ring-black transition-all"
                placeholder="Enter new password (min 8 characters)"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Confirm New Password
              </label>
              <input
                type="password"
                value={passwordData.confirmPassword}
                onChange={(e) => setPasswordData(prev => ({ ...prev, confirmPassword: e.target.value }))}
                className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-black focus:outline-none focus:ring-1 focus:ring-black transition-all"
                placeholder="Confirm new password"
              />
            </div>
            <button
              onClick={handlePasswordUpdate}
              disabled={savingPassword}
              className="mt-2 flex items-center gap-2 px-6 py-2 bg-black text-white text-sm rounded-lg hover:bg-gray-800 disabled:opacity-50 transition-all hover:scale-105 active:scale-95"
            >
              {savingPassword ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Lock className="h-4 w-4" />
              )}
              {savingPassword ? 'Updating...' : 'Update Password'}
            </button>
          </div>
        </div>
      )}

      {/* Business Tab */}
      {activeTab === 'business' && (
        <div className="bg-white shadow-sm border border-gray-200 rounded-xl p-6 space-y-6 hover:shadow-md transition-shadow">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Company Name
            </label>
            <input
              type="text"
              value={profileData.company_name || ''}
              onChange={(e) => setProfileData(prev => ({ ...prev, company_name: e.target.value }))}
              className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-black focus:outline-none focus:ring-1 focus:ring-black transition-all"
              placeholder="Your company name"
            />
          </div>

          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Industry
              </label>
              <select
                value={profileData.industry || ''}
                onChange={(e) => setProfileData(prev => ({ ...prev, industry: e.target.value }))}
                className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-black focus:outline-none focus:ring-1 focus:ring-black transition-all"
              >
                <option value="">Select industry</option>
                <option value="technology">Technology</option>
                <option value="finance">Finance</option>
                <option value="healthcare">Healthcare</option>
                <option value="retail">Retail</option>
                <option value="manufacturing">Manufacturing</option>
                <option value="consulting">Consulting</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Company Size
              </label>
              <select
                value={profileData.company_size || ''}
                onChange={(e) => setProfileData(prev => ({ ...prev, company_size: e.target.value }))}
                className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-black focus:outline-none focus:ring-1 focus:ring-black transition-all"
              >
                <option value="">Select size</option>
                <option value="1-10">1-10 employees</option>
                <option value="11-50">11-50 employees</option>
                <option value="51-200">51-200 employees</option>
                <option value="201-500">201-500 employees</option>
                <option value="500+">500+ employees</option>
              </select>
            </div>
          </div>

          <div className="pt-4 border-t border-gray-200 flex justify-end">
            <button
              onClick={handleSaveProfile}
              disabled={savingProfile}
              className="flex items-center gap-2 px-6 py-2 bg-black text-white text-sm rounded-lg hover:bg-gray-800 disabled:opacity-50 transition-all hover:scale-105 active:scale-95"
            >
              {savingProfile ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Save className="h-4 w-4" />
              )}
              {savingProfile ? 'Saving...' : 'Save Business Profile'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
