// frontend/src/components/AdminDashboard.tsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const AdminDashboard: React.FC = () => {
    const [users, setUsers] = useState<any[]>([]);
    const [groups, setGroups] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const navigate = useNavigate();

    useEffect(() => {
        const fetchAdminData = async () => {
            try {
                const token = localStorage.getItem('accessToken');
                if (!token) {
                    navigate('/');
                    return;
                }

                const response = await axios.get('http://127.0.0.1:8000/admin/dashboard/', {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                });
                setUsers(response.data.users);
                setGroups(response.data.groups);
                setLoading(false);
            } catch (err) {
                setError('Failed to fetch data. Make sure you have an Admin account.');
                setLoading(false);
                console.error(err);
            }
        };
        fetchAdminData();
    }, []);

    // --- Styles ---
    const containerStyle: React.CSSProperties = {
        padding: '40px 20px',
        maxWidth: '1000px',
        margin: '0 auto',
    };

    const headerStyle: React.CSSProperties = {
        fontSize: '32px',
        fontWeight: 'bold',
        marginBottom: '30px',
        color: '#2D3748',
        textAlign: 'center',
    };

    const sectionContainerStyle: React.CSSProperties = {
        display: 'flex',
        flexDirection: 'column',
        gap: '25px',
    };

    const cardStyle: React.CSSProperties = {
        padding: '25px',
        border: '1px solid #CBD5E0',
        borderRadius: '10px',
        boxShadow: '0 4px 8px rgba(0,0,0,0.1)',
        backgroundColor: 'white',
    };

    const listStyle: React.CSSProperties = {
        listStyleType: 'none',
        padding: '0',
    };

    const listItemStyle: React.CSSProperties = {
        padding: '10px',
        borderBottom: '1px solid #EDF2F7',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
    };
    
    const badgeStyle = (role: string): React.CSSProperties => {
        let color = '#718096'; // Gray
        if (role === 'Teacher') color = '#2B6CB0'; // Blue
        if (role === 'HOD/Admin') color = '#9B2C2C'; // Maroon
        
        return {
            display: 'inline-block',
            padding: '2px 8px',
            borderRadius: '10px',
            fontSize: '12px',
            fontWeight: 'bold',
            color: 'white',
            backgroundColor: color,
            marginLeft: '10px',
        };
    };

    // --- Render Logic ---
    if (loading) {
        return <div style={{ textAlign: 'center', paddingTop: '50px' }}>Loading admin data...</div>;
    }

    if (error) {
        return <div style={{ textAlign: 'center', paddingTop: '50px', color: 'red' }}>Error: {error}</div>;
    }

    return (
        <div style={containerStyle}>
            <h2 style={headerStyle}>User & Group Management</h2>
            
            <div style={sectionContainerStyle}>

                {/* All Users Section */}
                <div style={cardStyle}>
                    <h3 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '15px', color: '#4A5568' }}>System Users ({users.length})</h3>
                    <ul style={listStyle}>
                        {users?.map((user: any) => (
                            <li key={user.id} style={listItemStyle}>
                                <div>
                                    <strong>{user.username}</strong> - {user.email} 
                                </div>
                                <span style={badgeStyle(user.role)}>{user.role}</span>
                            </li>
                        ))}
                    </ul>
                </div>

                {/* All Groups Section */}
                <div style={cardStyle}>
                    <h3 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '15px', color: '#4A5568' }}>Project Groups ({groups.length})</h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                        {groups?.map((group: any) => (
                            <div key={group.id} style={{ padding: '15px', border: '1px solid #E2E8F0', borderRadius: '8px' }}>
                                <h4 style={{ fontSize: '18px', fontWeight: 'bolder', marginBottom: '5px', color: '#3182CE' }}>{group.name}</h4>
                                <p style={{ fontSize: '14px', color: '#718096' }}>{group.description}</p>
                                <div style={{ marginTop: '10px' }}>
                                    <p style={{ fontSize: '14px', marginBottom: '5px' }}>
                                        <strong>Teachers:</strong> {group.teachers.length > 0 ? group.teachers.map((t: any) => t.username).join(', ') : 'None Assigned'}
                                    </p>
                                    <p style={{ fontSize: '14px' }}>
                                        <strong>Students:</strong> {group.students.length > 0 ? group.students.map((s: any) => s.username).join(', ') : 'None Assigned'}
                                    </p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AdminDashboard;