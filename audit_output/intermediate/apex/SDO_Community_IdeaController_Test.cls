@isTest(SeeAllData=true)
private class SDO_Community_IdeaController_Test {
    
    static testMethod void unitTest(){
        //SDO_Community_IdeaController.getLoginURL('/login');
        SDO_Community_IdeaController.getCurrentCommunityZones();
        SDO_Community_IdeaController.getCurrentCommunityZoneIDs();
        SDO_Community_IdeaController.getMyIdeas();
        SDO_Community_IdeaController.getTotalIdeas(5, 'Popular', 1, SDO_Community_IdeaController.getCurrentCommunityZoneIDs()[0]);
        SDO_Community_IdeaController.getTotalIdeas(5, 'my', 1, SDO_Community_IdeaController.getCurrentCommunityZoneIDs()[0]);
        SDO_Community_IdeaController.getIdeasList(5, 'Popular', 1, SDO_Community_IdeaController.getCurrentCommunityZoneIDs()[0]);
        SDO_Community_IdeaController.getIdeasList(5, 'Recent', 1, SDO_Community_IdeaController.getCurrentCommunityZoneIDs()[0]);
        SDO_Community_IdeaController.getIdeasList(5, 'my', 1, SDO_Community_IdeaController.getCurrentCommunityZoneIDs()[0]);
        Community com = [select Id from Community limit 1];
        Idea newIdea = new Idea(Body='My Idea');
        newIdea.Title = 'Test Idea';
        newIdea.CommunityId = com.Id;
        insert newIdea;
        SDO_Community_IdeaController.getUserIdeas(newIdea.Id);
        SDO_Community_IdeaController.promoteIdea(newIdea.Id);
        SDO_Community_IdeaController.promoteFromIdeaDetails(newIdea.Id);
        SDO_Community_IdeaController.demoteIdea(newIdea.Id);
        SDO_Community_IdeaController.demoteFromIdeaDetails(newIdea.Id);
        SDO_Community_IdeaController.getIdea(newIdea.Id);
        
        IdeaComment newComment = new IdeaComment(IdeaId = newIdea.Id, CommentBody = 'Test Comment');
        insert newComment;
        
        SDO_Community_IdeaController.getComment(newIdea.Id);
        
        Vote newVote = new Vote(Type = 'Up', ParentId = newComment.Id);
        insert newVote;
        
        SDO_Community_IdeaController.unlikeThisComment(newIdea.Id, newVote.Id);
        SDO_Community_IdeaController.likeThisComment(newIdea.Id, newComment.Id);
        SDO_Community_IdeaController.postComment(newIdea.Id, 'Test Comment');
        SDO_Community_IdeaController.deleteThisComment(newIdea.Id, newComment.Id);
        SDO_Community_IdeaController.postIdea('Idea Title', 'Idea body', SDO_Community_IdeaController.getCurrentCommunityZoneIDs()[0]);
        SDO_Community_IdeaController.findSimilarIdeas('Idea Title');
        SDO_Community_IdeaController.isGuestUser();
        SDO_Community_IdeaController.getUserType();
    }
    
}