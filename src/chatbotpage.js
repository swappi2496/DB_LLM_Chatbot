import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useLocation } from 'react-router-dom';
import './chatbotpage.css';

function ChatbotPage() {
    const [message, setMessage] = useState('');
    const [messages, setMessages] = useState([]);
    const [tables, setTables] = useState([]);
    const [generatedQuery, setGeneratedQuery] = useState('');
    const [queryResult, setQueryResult] = useState('');
    const [loading, setLoading] = useState(false);

    const location = useLocation();
    const query = new URLSearchParams(location.search);
    const db = query.get('db');

    useEffect(() => {
        if (db) {
            fetchTables(db);
        } else {
            console.error('Database type is not defined.');
        }
    }, [db]);

    const fetchTables = async (db) => {
        try {
            const res = await axios.get('http://localhost:5000/api/tables', { params: { db } });
            setTables(res.data.tables);
        } catch (error) {
            console.error("Error fetching tables:", error.response ? error.response.data : error.message);
            setMessages([...messages, { role: 'bot', content: `Error fetching tables: ${error.response ? error.response.data : error.message}` }]);
        }
    };
    

    const handleSendMessage = async (msg) => {
        if (!msg.trim()) {
            alert('Please enter a message.');
            return;
        }

        const newMessages = [...messages, { role: 'user', content: msg }];
        setMessages(newMessages);
        setMessage('');
        setLoading(true);

        try {
            const res = await axios.post('http://localhost:5000/api/chat', { 
                message: msg, 
                db_type: db 
            });
            //console.log(res.data.message);
            const botMessage = res.data.message || '';
            const query = res.data.query || '';
            const result = res.data.results ? formatQueryResult(res.data.results) : '';

            setGeneratedQuery(query); // Store the generated query
            setQueryResult(result); // Store the query result
            if (botMessage) {
                setMessages([...newMessages, { role: 'bot', content: botMessage }]);
            }
        } catch (error) {
            const errorMessage = error.response ? error.response.data.error : error.message;
            setMessages([...newMessages, { role: 'bot', content: `Error: ${errorMessage}` }]);
        } finally {
            setLoading(false);
        }
    };

    const handleTableClick = (table) => {
        const tableMessage = `Show information about ${table} table in ${db} database.`;
        handleSendMessage(tableMessage);
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault(); // Prevents adding newline
            handleSendMessage(message);
        }
    };

    const handleExecuteQuery = async () => {
        setLoading(true);
        try {
            const res = await axios.post('http://localhost:5000/api/execute_query', { 
                query: generatedQuery, 
                db_type: db 
            });
            const columns = res.data.columns || [];
            const result = res.data.result ? formatQueryResult(columns, res.data.result) : 'No results found';
            setQueryResult(result);
        } catch (error) {
            const errorMessage = error.response ? error.response.data.error : error.message;
            setQueryResult(`Error: ${errorMessage}`);
        } finally {
            setLoading(false);
        }
    };
    
    const formatQueryResult = (columns, result) => {
        if (columns.length > 0 && result.length > 0) {
            let table = '<table border="1"><thead><tr>';
            // Create table headers
            for (let col of columns) {
                table += `<th>${col}</th>`;
            }
            table += '</tr></thead><tbody>';
            // Create table rows
            for (let row of result) {
                table += '<tr>';
                for (let cell of row) {
                    table += `<td>${cell}</td>`;
                }
                table += '</tr>';
            }
            table += '</tbody></table>';
            return table;
        } else {
            return 'No results found';
        }
    };

    useEffect(() => {
        const chatContainer = document.querySelector('.chat-messages');
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }, [messages, queryResult]);

    return (
        <div className="chatbot-page">
            <div className="left-panel">
                <h2>Connected Database: {db}</h2>
                <div className="tables-list">
                    <h3>Tables:</h3>
                    <ul>
                        {tables.map((table, index) => (
                            <li key={index} onClick={() => handleTableClick(table)}>{table}</li>
                        ))}
                    </ul>
                </div>
            </div>
            <div className="chat-container">
                <div className="chat-header">
                    Chatbot for {db}
                </div>
                <div className="chat-messages">
                    {messages.map((msg, index) => (
                        <div key={index} className={`message ${msg.role === 'user' ? 'user-message' : 'bot-message'}`}>
                            <div dangerouslySetInnerHTML={{ __html: msg.content }} />
                        </div>
                    ))}
                    {generatedQuery && (
                        <div className="message bot-message">
                            <h3>Generated Query:</h3>
                            <pre>{generatedQuery}</pre>
                            <button 
                                className="execute-query-button"
                                onClick={handleExecuteQuery}
                                disabled={loading}
                            >
                                {loading ? 'Executing...' : 'Execute Query'}
                            </button>
                        </div>
                    )}
                    {queryResult && (
                        <div className="message bot-message">
                            <h3>Query Result:</h3>
                            <div dangerouslySetInnerHTML={{ __html: queryResult }} />
                        </div>
                    )}
                </div>
                <div className="chat-input">
                    <textarea 
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder="Ask me anything about the database schema, tables, etc."
                    />
                    <button 
                        type="button" 
                        onClick={() => handleSendMessage(message)}
                        disabled={loading}
                    >
                        {loading ? 'Sending...' : 'Send'}
                    </button>
                </div>
            </div>
        </div>
    );
}

export default ChatbotPage;
