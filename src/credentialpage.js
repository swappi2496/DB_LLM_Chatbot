import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import './credentialpage.css';

function CredentialsPage() {
    const navigate = useNavigate();
    const location = useLocation();
    const query = new URLSearchParams(location.search);
    const db = query.get('db');
console.log(query);
    const [credentials, setCredentials] = useState({
        host: '',
        port: '',
        user: '',
        password: '',
        database: '',
    });

    const handleChange = (e) => {
        const { name, value } = e.target;
        setCredentials((prev) => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const response = await axios.post(`http://localhost:5000/connect/${db.toLowerCase()}`, credentials);
            alert(response.data.message);
            navigate(`/chat?db=${db}`);
        } catch (error) {
            alert(`Error: ${error.response ? error.response.data.error : error.message}`);
        }
    };

    return (
        <div className="credentials-page">
            <h1>Enter {db} Credentials</h1>
            <form onSubmit={handleSubmit}>
                <label>
                    Host:
                    <input type="text" name="host" value={credentials.host} onChange={handleChange} required />
                </label>
                <label>
                    Port:
                    <input type="text" name="port" value={credentials.port} onChange={handleChange} required />
                </label>
                <label>
                    User:
                    <input type="text" name="user" value={credentials.user} onChange={handleChange} required />
                </label>
                <label>
                    Password:
                    <input type="password" name="password" value={credentials.password} onChange={handleChange} required />
                </label>
                <label>
                    Database:
                    <input type="text" name="database" value={credentials.database} onChange={handleChange} required />
                </label>
                <button type="submit">Connect</button>
            </form>
        </div>
    );
}

export default CredentialsPage;
