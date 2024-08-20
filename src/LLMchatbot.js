import React, { useState } from 'react';
import axios from 'axios';
import { FaPaperPlane } from 'react-icons/fa';
import './App.css';

function App() {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleSend = async () => {
        if (input.trim() === '') return;

        const userMessage = { sender: 'user', text: input };
        setMessages([...messages, userMessage]);
        setInput('');
        setLoading(true);
        setError(null);

        try {
            const response = await axios.post('http://localhost:5000/api/chat', { message: input });
            const botMessage = { sender: 'bot', text: response.data.message };
            setMessages([...messages, userMessage, botMessage]);
        } catch (error) {
            setError('Failed to get a response from the server');
            console.error('Error sending message:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="App">
            <div className="chatbox">
                {messages.map((msg, index) => (
                    <div key={index} className={`message ${msg.sender}`}>
                        {msg.text}
                    </div>
                ))}
                {loading && <div className="loading">Loading...</div>}
            </div>
            {error && <div className="error">{error}</div>}
            <div className="inputbox">
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                    disabled={loading}
                />
                <button onClick={handleSend} disabled={loading}>
                    <FaPaperPlane />
                </button>
            </div>
        </div>
    );
}

export default App;
