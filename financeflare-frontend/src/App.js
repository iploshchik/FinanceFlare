import React, { useEffect, useState } from "react";
import api from "./api";

function App() {
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    api.get("/transactions/summary/")
        .then((response) => setSummary(response.data))
        .catch((error) => console.error("Error fetching summary:", error));
  }, []);

  return (
      <div className="App">
        <h1>FinanceFlare</h1>
        {summary ? (
            <div>
              <p>Total Income: {summary.total_income}</p>
              <p>Total Expenses: {summary.total_expenses}</p>
              <p>Net Balance: {summary.net_balance}</p>
            </div>
        ) : (
            <p>Loading...</p>
        )}
      </div>
  );
}

export default App;