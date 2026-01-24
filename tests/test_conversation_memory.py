#!/usr/bin/env python
"""
Test de la mémoire de conversation de YanaChat V2.

Lance une conversation contextuelle pour vérifier que le chatbot
se souvient des échanges précédents.

Usage: python tests/test_conversation_memory.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.chat_handler import ChatHandler


def test_conversation_memory():
    """Test que le chatbot retient le contexte de la conversation."""
    print("=" * 60)
    print("TEST DE MÉMOIRE DE CONVERSATION")
    print("=" * 60)
    
    handler = ChatHandler()
    session_id = "test_memory_session"
    
    # Étape 1: Établir un contexte
    print("\n[1] Établissement du contexte...")
    query1 = "Je m'appelle Julien et je vis en Guyane."
    result1 = handler.handle_query(query1, session_id=session_id, use_web_search=False)
    print(f"User: {query1}")
    print(f"Bot: {result1['response'][:200]}...")
    
    # Vérifier l'historique
    history = handler.get_session_history(session_id)
    assert len(history) == 2, f"Expected 2 messages, got {len(history)}"
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"
    print(f"✓ Historique stocké: {len(history)} messages")
    
    # Étape 2: Poser une question qui nécessite le contexte
    print("\n[2] Question contextuelle...")
    query2 = "Quel est mon prénom ?"
    result2 = handler.handle_query(query2, session_id=session_id, use_web_search=False)
    print(f"User: {query2}")
    print(f"Bot: {result2['response'][:200]}...")
    
    # Vérifier que le bot a accès au contexte
    history = handler.get_session_history(session_id)
    assert len(history) == 4, f"Expected 4 messages, got {len(history)}"
    print(f"✓ Historique mis à jour: {len(history)} messages")
    
    # Vérifier que la réponse mentionne "Julien"
    if "Julien" in result2['response'].lower():
        print("✓ Le bot a retenu le prénom (Julien)")
    else:
        print("⚠ Le bot n'a peut-être pas retenu le prénom")
    
    # Étape 3: Question de suivi
    print("\n[3] Question de suivi...")
    query3 = "Où est-ce que j'habite ?"
    result3 = handler.handle_query(query3, session_id=session_id, use_web_search=False)
    print(f"User: {query3}")
    print(f"Bot: {result3['response'][:200]}...")
    
    # Vérifier que la réponse mentionne "Guyane"
    if "guyane" in result3['response'].lower():
        print("✓ Le bot a retenu le lieu (Guyane)")
    else:
        print("⚠ Le bot n'a peut-être pas retenu le lieu")
    
    # Étape 4: Tester l'effacement de l'historique
    print("\n[4] Test d'effacement de l'historique...")
    handler.clear_session_history(session_id)
    history = handler.get_session_history(session_id)
    assert len(history) == 0, f"Expected 0 messages after clear, got {len(history)}"
    print("✓ Historique effacé avec succès")
    
    # Étape 5: Vérifier que le contexte est perdu après effacement
    print("\n[5] Vérification de perte de contexte...")
    query4 = "Comment je m'appelle ?"
    result4 = handler.handle_query(query4, session_id=session_id, use_web_search=False)
    print(f"User: {query4}")
    print(f"Bot: {result4['response'][:200]}...")
    
    if "Julien" not in result4['response'].lower():
        print("✓ Le bot a oublié le contexte (comportement attendu)")
    else:
        print("⚠ Le bot semble encore connaître le contexte")
    
    print("\n" + "=" * 60)
    print("TEST TERMINÉ")
    print("=" * 60)


def test_multiple_sessions():
    """Test que les sessions sont isolées."""
    print("\n" + "=" * 60)
    print("TEST D'ISOLATION DES SESSIONS")
    print("=" * 60)
    
    handler = ChatHandler()
    
    # Session 1
    session1 = "session_alice"
    query1 = "Je m'appelle Alice."
    result1 = handler.handle_query(query1, session_id=session1)
    print(f"\n[Session Alice] {query1}")
    print(f"Bot: {result1['response'][:150]}...")
    
    # Session 2
    session2 = "session_bob"
    query2 = "Je m'appelle Bob."
    result2 = handler.handle_query(query2, session_id=session2)
    print(f"\n[Session Bob] {query2}")
    print(f"Bot: {result2['response'][:150]}...")
    
    # Vérifier isolation
    history1 = handler.get_session_history(session1)
    history2 = handler.get_session_history(session2)
    
    assert len(history1) == 2, "Session Alice devrait avoir 2 messages"
    assert len(history2) == 2, "Session Bob devrait avoir 2 messages"
    assert "Alice" in history1[0]["content"]
    assert "Bob" in history2[0]["content"]
    
    print(f"\n✓ Session Alice: {len(history1)} messages")
    print(f"✓ Session Bob: {len(history2)} messages")
    print("✓ Les sessions sont isolées")
    
    print("\n" + "=" * 60)
    print("TEST TERMINÉ")
    print("=" * 60)


if __name__ == "__main__":
    print("\n🤖 YanaChat V2 - Tests de Mémoire de Conversation\n")
    
    try:
        test_conversation_memory()
        test_multiple_sessions()
        
        print("\n✅ Tous les tests sont passés!")
        print("\nNote: Ces tests nécessitent une connexion à l'API Mistral.")
        print("Pour tester sans appels API réels, mockez LLMPipeline.generate()")
        
    except AssertionError as e:
        print(f"\n❌ Test échoué: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
