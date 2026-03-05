public class MicrobatchSelfRegController {
    public String firstName {get; set;}
    public String lastName {get; set;}
    public String email {get; set;}
    public String communityNickname {get; set { communityNickname = value == null ? value : value.trim(); } }

    public MicrobatchSelfRegController() {
        String expid = ApexPages.currentPage().getParameters().get('expid');
        if (expId != null) {
            Site.setExperienceId(expId);
        }
    }

    public PageReference registerUser() {
        String userName = email;
        String accountName;
        String contactName;
        String profileId = null;
        String UUID;

        User u = new User();
        u.Username = userName;
        u.Email = email;
        u.FirstName = firstName;
        u.LastName = lastName;
        u.CommunityNickname = communityNickname;
        u.ProfileId = profileId;
        u.LocaleSidKey = 'en_US';
        u.TimeZoneSidKey = 'GMT';
        u.LanguageLocaleKey = 'en_US';
        u.EmailEncodingKey = 'UTF-8';

        Account acc = new Account();
        acc.Name = 'Account for ' + lastName;
        Contact c = new Contact();
        c.lastName = lastName;

        try {
            UUID =  Network.createExternalUserAsync(u, c,acc);
        } catch(Site.ExternalUserCreateException ex) {
            List<String> errors = ex.getDisplayMessages();
            for (String error : errors)  {
                ApexPages.addMessage(new ApexPages.Message(ApexPages.Severity.ERROR, error));
            }
            System.debug(ex.getMessage());
        }
        if (UUID != null) {
           PageReference page = System.Page.CommunitiesSelfRegConfirm;
           page.setRedirect(true);
           return page;
        }
        return null;
    }
}