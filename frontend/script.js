document.addEventListener("DOMContentLoaded", function(){
    document.getElementById('scrapeForm').addEventListener('submit', async (e) => {
        e.preventDefault();

        let spreadsheetId = document.getElementById("spreadsheetId").value;
        let user = document.getElementById("user").value;
        let submitButton = document.querySelector("button[type='submit']");

        if(!spreadsheetId || !user) {
            showNotification("Please provide the spreadsheet ID and/or the user.");
            return;
        }

        console.log(spreadsheetId);
        console.log(user);
        console.log(submitButton);
        console.log("Start scrapping button clicked");
    });
 }
)
