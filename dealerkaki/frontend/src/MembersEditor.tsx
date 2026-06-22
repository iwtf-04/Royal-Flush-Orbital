import { useEffect, useState } from 'react';

interface UserRecord {
  id: number;
  username: string;
  role: string;
  created_at: string;
}

interface Props {
  authToken: string | null;
}

const roleOptions = [
  'admin',
  'dealer',
  'inventory manager',
  'frontline staff',
];

function MembersEditor({ authToken }: Props) {
  const [users, setUsers] = useState<UserRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newUsername, setNewUsername] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newRole, setNewRole] = useState('inventory manager');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const fetchUsers = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch('/api/users', {
        headers: {
          Authorization: authToken ? `Bearer ${authToken}` : '',
        },
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error('detail' in data ? data.detail : 'Failed to fetch users');
      }
      setUsers(data.users || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load users');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleAddUser = async () => {
    setError('');
    setMessage('');
    if (!newUsername || !newPassword) {
      setError('Please enter username and password.');
      return;
    }

    try {
      const response = await fetch('/api/users', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: authToken ? `Bearer ${authToken}` : '',
        },
        body: JSON.stringify({
          username: newUsername.trim(),
          password: newPassword,
          role: newRole,
        }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error('detail' in data ? data.detail : 'Failed to add user');
      }
      setMessage(`User ${data.user.username} created successfully.`);
      setNewUsername('');
      setNewPassword('');
      setNewRole('inventory manager');
      fetchUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to add user');
    }
  };

  const handleDeleteUser = async (userId: number, username: string) => {
    const confirmed = window.confirm(`Remove user ${username} from the system?`);
    if (!confirmed) return;
    setError('');
    setMessage('');
    try {
      const response = await fetch(`/api/users/${userId}`, {
        method: 'DELETE',
        headers: {
          Authorization: authToken ? `Bearer ${authToken}` : '',
        },
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error('detail' in data ? data.detail : 'Failed to remove user');
      }
      setMessage(`User ${username} removed.`);
      fetchUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to remove user');
    }
  };

  return (
    <div className="members-editor">
      <h2>Edit Members</h2>
      <p>Only dealer and admin users can manage team accounts here.</p>

      {loading && <p>Loading users...</p>}
      {error && <p className="error-message">{error}</p>}
      {message && <p className="success-message">{message}</p>}

      <section className="members-table-section">
        <h3>Current Users</h3>
        <table className="members-table">
          <thead>
            <tr>
              <th>Username</th>
              <th>Role</th>
              <th>Created</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id}>
                <td>{user.username}</td>
                <td>{user.role}</td>
                <td>{new Date(user.created_at).toLocaleString()}</td>
                <td>
                  <button type="button" className="table-action-button remove-button" onClick={() => handleDeleteUser(user.id, user.username)}>
                    Remove
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="members-form-section">
        <div className="members-form-header">
          <h3>Add New User</h3>
          <button type="button" className="secondary-button" onClick={() => setShowAddForm((open) => !open)}>
            {showAddForm ? 'Hide Form' : 'Add Member'}
          </button>
        </div>

        {showAddForm && (
          <div className="member-form-inner">
            <label>
              Username
              <input type="text" value={newUsername} onChange={(e) => setNewUsername(e.target.value)} />
            </label>

            <label>
              Password
              <input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
            </label>

            <label>
              Role
              <select value={newRole} onChange={(e) => setNewRole(e.target.value)}>
                {roleOptions.map((role) => (
                  <option key={role} value={role}>{role}</option>
                ))}
              </select>
            </label>

            <button type="button" className="primary-button" onClick={handleAddUser}>
              Add User
            </button>
          </div>
        )}
      </section>
    </div>
  );
}

export default MembersEditor;
