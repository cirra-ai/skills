public with sharing class SDO_Community_LandingController {
    public PageReference forwardToStartPage() {
        return Network.communitiesLanding();
    }
    public SDO_Community_LandingController() {}
}