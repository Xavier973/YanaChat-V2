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


def test_conversation_memory(use_web_search=False):
    """Test que le chatbot retient le contexte de la conversation."""
    mode_label = "AVEC WEB SEARCH" if use_web_search else "SANS WEB SEARCH"
    print("=" * 60)
    print(f"TEST DE MÉMOIRE DE CONVERSATION - {mode_label}")
    print("=" * 60)
    
    handler = ChatHandler()
    session_id = f"test_memory_session_{mode_label.replace(' ', '_').lower()}"
    
    # Étape 1: Établir un contexte
    print("\n[1] Établissement du contexte...")
    query1 = "Je m'appelle Julien et je vis en Guyane."
    result1 = handler.handle_query(query1, session_id=session_id, use_web_search=use_web_search)
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
    result2 = handler.handle_query(query2, session_id=session_id, use_web_search=use_web_search)
    print(f"User: {query2}")
    print(f"Bot: {result2['response'][:200]}...")
    
    # Vérifier que le bot a accès au contexte
    history = handler.get_session_history(session_id)
    assert len(history) == 4, f"Expected 4 messages, got {len(history)}"
    print(f"✓ Historique mis à jour: {len(history)} messages")
    
    # Vérifier que la réponse mentionne "Julien"
    if "julien" in result2['response'].lower():
        print("✓ Le bot a retenu le prénom (Julien)")
    else:
        print("⚠ Le bot n'a peut-être pas retenu le prénom")
    
    # Étape 3: Question de suivi
    print("\n[3] Question de suivi...")
    query3 = "Où est-ce que j'habite ?"
    result3 = handler.handle_query(query3, session_id=session_id, use_web_search=use_web_search)
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
    result4 = handler.handle_query(query4, session_id=session_id, use_web_search=use_web_search)
    print(f"User: {query4}")
    print(f"Bot: {result4['response'][:200]}...")
    
    if "julien" not in result4['response'].lower():
        print("✓ Le bot a oublié le contexte (comportement attendu)")
    else:
        print("⚠ Le bot semble encore connaître le contexte")
    
    print("\n" + "=" * 60)
    print(f"TEST TERMINÉ - {mode_label}")
    print("=" * 60)


def test_multiple_sessions(use_web_search=False):
    """Test que les sessions sont isolées."""
    mode_label = "AVEC WEB SEARCH" if use_web_search else "SANS WEB SEARCH"
    print("\n" + "=" * 60)
    print(f"TEST D'ISOLATION DES SESSIONS - {mode_label}")
    print("=" * 60)
    
    handler = ChatHandler()
    
    # Session 1
    session1 = f"session_alice_{mode_label.replace(' ', '_').lower()}"
    query1 = "Je m'appelle Alice."
    result1 = handler.handle_query(query1, session_id=session1, use_web_search=use_web_search)
    print(f"\n[Session Alice] {query1}")
    print(f"Bot: {result1['response'][:150]}...")
    
    # Session 2
    session2 = f"session_bob_{mode_label.replace(' ', '_').lower()}"
    query2 = "Je m'appelle Bob."
    result2 = handler.handle_query(query2, session_id=session2, use_web_search=use_web_search)
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
    print(f"TEST TERMINÉ - {mode_label}")
    print("=" * 60)


if __name__ == "__main__":
    print("\n🤖 YanaChat V2 - Tests de Mémoire de Conversation\n")
    
    try:
        # Tests SANS web search
        print("\n" + "🔵" * 30)
        print("PHASE 1: Tests sans web search")
        print("🔵" * 30 + "\n")
        test_conversation_memory(use_web_search=False)
        test_multiple_sessions(use_web_search=False)
        
        # Tests AVEC web search
        print("\n" + "🟢" * 30)
        print("PHASE 2: Tests avec web search")
        print("🟢" * 30 + "\n")
        test_conversation_memory(use_web_search=True)
        test_multiple_sessions(use_web_search=True)
        
        print("\n" + "=" * 60)
        print("✅ Tous les tests sont passés!")
        print("=" * 60)
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
