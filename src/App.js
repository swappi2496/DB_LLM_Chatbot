import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import LandingPage from './landingpage';
import CredentialsPage from './credentialpage';
import ChatbotPage from './chatbotpage';
import './App.css';

function App() {
    return (
        <Router>
            <div className="App">
                <Routes>
                    <Route path="/" element={<LandingPage />} />
                    <Route path="/credentials" element={<CredentialsPage />} />
                    <Route path="/chat" element={<ChatbotPage />} />
                </Routes>
            </div>
        </Router>
    );
}

export default App;
