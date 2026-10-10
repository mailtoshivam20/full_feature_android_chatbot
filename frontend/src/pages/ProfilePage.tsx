import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";
import { authApi } from "@/api/auth";
import client from "@/api/client";
import toast from "react-hot-toast";

export default function ProfilePage() {
  const navigate = useNavigate();
  const { user, loadUser } = useAuthStore();
  const [username, setUsername] = useState(user?.username || "");
  const [currentPw, setCurrentPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [saving, setSaving] = useState(false);

  const handleUpdateUsername = async () => {
    setSaving(true);
    try {
      await client.put("/users/me", { username });
      await loadUser();
      toast.success("Username updated");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Update failed");
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async () => {
    setSaving(true);
    try {
      await authApi.changePassword({ current_password: currentPw, new_password: newPw });
      setCurrentPw("");
      setNewPw("");
      toast.success("Password changed");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Password change failed");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-lg mx-auto">
        <button onClick={() => navigate(-1)} className="text-sm text-blue-600 mb-4">
          ← Back
        </button>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">Profile</h1>

        <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6 space-y-6">
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">{user?.email}</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Username</label>
            <div className="flex gap-2">
              <input
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="flex-1 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={handleUpdateUsername}
                disabled={saving}
                className="px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm rounded-lg transition"
              >
                Save
              </button>
            </div>
          </div>

          <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
            <h2 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Change Password</h2>
            <div className="space-y-2">
              <input
                type="password"
                placeholder="Current password"
                value={currentPw}
                onChange={(e) => setCurrentPw(e.target.value)}
                className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <input
                type="password"
                placeholder="New password"
                value={newPw}
                onChange={(e) => setNewPw(e.target.value)}
                className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={handleChangePassword}
                disabled={saving || !currentPw || !newPw}
                className="w-full px-3 py-2 bg-gray-700 hover:bg-gray-800 disabled:opacity-50 text-white text-sm rounded-lg transition"
              >
                Change Password
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
