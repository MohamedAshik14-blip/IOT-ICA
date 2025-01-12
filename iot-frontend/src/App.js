document.addEventListener("DOMContentLoaded", () => {
      const API_BASE_URL = "http://localhost:3001";
      const pubnub = new PubNub({
        publishKey: "pub-c-45bab202-c191-4fbe-a1d0-2628df540689",
        subscribeKey: "sub-c-6963e588-282e-41ec-8194-9b6710e52ad3",
        userId: "temperature-subscriber",
      });

      let token = ""; 
      let isAuthenticated = false;
      let historyData = [];

      const authBtn = document.getElementById("auth-btn");
      const usernameInput = document.getElementById("username");
      const passwordInput = document.getElementById("password");
      const toggleAuthLink = document.getElementById("toggle-auth");
      const authContainer = document.querySelector(".auth-container");
      const dashboardContainer = document.querySelector(".dashboard");                   

   toggleAuthLink.addEventListener("click", () => {
      const isLoginForm = authBtn.textContent === "Login";
      authBtn.textContent = isLoginForm ? "Register" : "Login";
      document.getElementById("auth-header").textContent = isLoginForm ? "Register" : "Login";
    });

 authBtn.addEventListener("click", () => {
  if (!usernameInput.value || !passwordInput.value) {
    alert("Please fill out both fields!");
    return;
  }

  
  if (authBtn.textContent === "Login") {
    handleAuth("login", "Logged in successfully!");
  } else if (authBtn.textContent === "Register") {
    handleAuth("register", "Registration successful!");
  }
});

      
      const handleAuth = async (action, successMessage) => {
        const url = action === "login" ? "/api/login" : "/api/register";
        try {
          const response = await fetch(`${API_BASE_URL}${url}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              username: usernameInput.value,
              password: passwordInput.value,
            }),
          });

          const data = await response.json();
          if (response.ok) {
            if (action === "login") {
              token = data.token;
              isAuthenticated = true;
              dashboardContainer.style.display = "block";
              document.getElementById("footer").style.display = "block";
              authContainer.style.display = "none";
            
              document.getElementById("logout-btn").style.display = "inline-block";
              document.getElementById("view-history-btn").style.display = "inline-block";
              fetchData();
              setInterval(fetchData, 5000); 
            } else {
              alert(successMessage);
              toggleAuthLink.click();
            }
          } else {
            alert("Authentication failed!");
          }
	} catch (error) {
          console.error("Authentication error:", error);
        }
      };
	 const updateLatestData = (data) => {
        document.getElementById("latest-temp").innerText = data.temperature;
        document.getElementById("latest-humidity").innerText = data.humidity;
        document.getElementById("latest-timestamp").innerText = data.timestamp;
      };

  
      const fetchData = async () => {
        if (isAuthenticated) {
          try {
            const response = await fetch(`${API_BASE_URL}/api/temperatures`, {
              headers: { Authorization: `Bearer ${token}` },
            });
            const latestResponse = await response.json();
            updateLatestData(latestResponse);

            const historyResponse = await fetch(`${API_BASE_URL}/api/history`, {
              headers: { Authorization: `Bearer ${token}` },
            });
            const historyResponseData = await historyResponse.json();
            historyData = historyResponseData;
            updateHistoryTable();
          } catch (error) {
            console.error("Error fetching data:", error);
          }
        }
      };

     
      const updateHistoryTable = () => {
        const historyTableBody = document.getElementById("history-table-body");
        historyTableBody.innerHTML = historyData
          .map(
            (record) => `
            <tr>
              <td>${record.timestamp}</td>
              <td>${record.temperature}</td>
              <td>${record.humidity}</td>
            </tr>`
          )
          .join("");
      };
	  document.getElementById("view-history-btn").addEventListener("click", () => {
        const historySection = document.querySelector(".history-section");
        historySection.style.display = historySection.style.display === "none" ? "block" : "none";
      });

	  document.getElementById("logout-btn").addEventListener("click", () => {
        isAuthenticated = false;
        token = "";
        authContainer.style.display = "block";
        dashboardContainer.style.display = "none";
        document.getElementById("footer").style.display = "none"; 
        document.getElementById("view-history-btn").style.display = "none"; 
        document.getElementById("logout-btn").style.display = "none"; 
      });

    });
    
