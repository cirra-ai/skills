global class SDO_Service_BotsFindContact 
{
    @InvocableMethod(label='Einstein Chatbots - Find Contact By LiveChatTranscript' description='Returns a Contact for the specified LiveChatTranscript.')
    global static List<Contact> getContactsFromTranscript(List<LiveChatTranscript> transcripts) 
    {   
        List<Contact> listContacts = new List<Contact>();   
        for (LiveChatTranscript currentTranscript : transcripts)
        {
            if (currentTranscript != null && String.IsNotBlank(currentTranscript.Id))
            {
                List<Contact> Contacts = new List<Contact>();
                if (currentTranscript.ContactId != null){
                    Contacts = [SELECT Id, FirstName, LastName, Email, Phone, Title, MailingAddress FROM Contact WHERE Id = :currentTranscript.ContactId LIMIT 1];
                } else {
                    String firstName = 'Lauren';
                    String lastName = 'Bailey';
                    Contacts = [SELECT Id, FirstName, LastName, Email, Phone, Title, MailingAddress FROM Contact WHERE FirstName = :firstName AND LastName = :lastName LIMIT 1];
                }
                if (Contacts != null && Contacts.size() > 0)
                {
                    Contact sampleContact = Contacts[0];
                    return Contacts;
                }
            }
        }
                        
        return new List<Contact>{new Contact()};
    }        
}