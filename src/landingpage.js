import React from 'react';
import { useNavigate } from 'react-router-dom';
import './landingpage.css';

function LandingPage() {
    const navigate = useNavigate();

    const handleDatabaseClick = (db) => {
        navigate(`/credentials?db=${db}`);
    };

    return (
        <div className="landing-page">
            <h1>Database Design Using Large Language Model</h1>
            <div className="databases">
                <div className="database-option" onClick={() => handleDatabaseClick('PostgreSQL')}>
                    <img src="postgre.svg" alt="PostgreSQL" />
                    <p>Connect to PostgreSQL</p>
                </div>
                <div className="database-option" onClick={() => handleDatabaseClick('MongoDB')}>
                    <img src="mongodb.svg" alt="MongoDB" />
                    <p>Connect to MongoDB</p>
                </div>
                <div className="database-option" onClick={() => handleDatabaseClick('MySQL')}>
                    <img src="mysql.svg" alt="MySQL" />
                    <p>Connect to MySQL</p>
                </div>
                <div className="database-option" onClick={() => handleDatabaseClick('SQLite')}>
                    <img src="sqlite-icon.svg" alt="SQLite" />
                    <p>Connect to SQLite</p>
                </div>
            </div>
        </div>
    );
}

export default LandingPage;
