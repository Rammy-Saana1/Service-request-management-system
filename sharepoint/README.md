# SharePoint assets

`provision-ServiceRequests.ps1` creates the schema idempotently. `sample-requests.csv` contains fictional, non-routable `contoso.example` addresses; replace them with licensed test users before import.

The sample CSV includes expected triage fields so it can support gallery screenshots immediately. For an end-to-end flow demo, create a new item with only title, description, and requester so the automation supplies the remaining fields.
