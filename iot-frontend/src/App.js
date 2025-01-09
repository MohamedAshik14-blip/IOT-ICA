import React, { useState, useEffect } from "react";
import PubNub from "pubnub";
import "./App.css"; 
 function App() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [token, setToken] = useState("");

const API_BASE_URL = "http://localhost:3001";
useEffect(() => {
    let interval;
    if (isAuthenticated) {
      interval = setInterval(() => {
        fetch(`${API_BASE_URL}/api/temperatures`, {
          headers: { Authorization: `Bearer ${token}` },
        })
          .then((response) => response.json())
          .then(setLatestData)
          .catch((error) => console.error("Error fetching latest data:", error));

        fetch(`${API_BASE_URL}/api/history`, {
          headers: { Authorization: `Bearer ${token}` },
        })
          .then((response) => response.json())
          .then(setHistoryData)
          .catch((error) => console.error("Error fetching historical data:", error));
      }, 5000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isAuthenticated, token]);

  const handleAuth = async (url, successMessage) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/${url}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();
      if (response.ok) {
        if (url === "login") {
          setToken(data.token);
          setIsAuthenticated(true);
        }
        alert(successMessage);
      } else {
        alert(data.message || "Error occurred");
      }
    } catch (error) {
      console.error("Error:", error);
      alert("Error occurred");
    }
  };

    return (
    <div className="App">
 {!isAuthenticated ? (
        <div className="auth-container">
          <h2>{isRegister ? "Register" : "Login"}</h2>
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <button
            className="btn primary"
            onClick={() =>
              handleAuth(isRegister ? "register" : "login", isRegister ? "Registered successfully!" : "Logged in successfully!")
            }
          >
            {isRegister ? "Register" : "Login"}
          </button>
          <p className="toggle-auth" onClick={() => setIsRegister(!isRegister)}>
            {isRegister ? "Switch to Login" : "Switch to Register"}
          </p>
        </div>
      ) : (
        <>
 </div>
  );
}

export default App;
