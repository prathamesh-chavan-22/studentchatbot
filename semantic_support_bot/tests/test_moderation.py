from app.moderation import ContentModerator

def test_moderation():
    moderator = ContentModerator()
    
    # Test English
    assert moderator.is_appropriate("This is clean")[0] == True
    assert moderator.is_appropriate("This is fuck")[0] == False
    
    # Test Hindi
    assert moderator.is_appropriate("यह साफ है")[0] == True
    assert moderator.is_appropriate("साला")[0] == False
    
    # Test Marathi
    assert moderator.is_appropriate("हे स्वच्छ आहे")[0] == True
    assert moderator.is_appropriate("मूर्ख")[0] == False
    
    print("Moderation tests passed!")

if __name__ == "__main__":
    test_moderation()
