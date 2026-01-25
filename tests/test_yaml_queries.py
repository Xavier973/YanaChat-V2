"""
Test script pour exécuter toutes les queries du fichier test_queries.yaml
Lance chaque question contre l'API YanaChat et affiche les résultats.
"""
import sys
import time
from pathlib import Path
import yaml
import requests
from typing import Dict, List

# Ajouter src/ au path pour imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Couleurs pour terminal
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def load_queries(yaml_path: Path) -> List[str]:
    """Charge les queries depuis le fichier YAML."""
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data.get('queries', [])


def test_query(query: str, api_url: str = "http://localhost:8000/api/chat", 
               web_search: bool = False, session_id: str = "test_session") -> Dict:
    """
    Teste une query contre l'API YanaChat.
    
    Args:
        query: La question à poser
        api_url: URL de l'API
        web_search: Active la recherche web via Mistral Agents
        session_id: ID de session pour mémoire conversation
    
    Returns:
        Dict avec status, response, temps, etc.
    """
    start_time = time.time()
    
    try:
        response = requests.post(
            api_url,
            json={
                "query": query,
                "session_id": session_id,
                "web_search": web_search
            },
            timeout=120  # 2 minutes max (agents API est lent)
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "success",
                "response": data.get("response", ""),
                "elapsed": elapsed,
                "status_code": response.status_code
            }
        else:
            return {
                "status": "error",
                "error": f"HTTP {response.status_code}: {response.text}",
                "elapsed": elapsed,
                "status_code": response.status_code
            }
    
    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        return {
            "status": "timeout",
            "error": "Request timeout (>120s)",
            "elapsed": elapsed
        }
    
    except Exception as e:
        elapsed = time.time() - start_time
        return {
            "status": "error",
            "error": str(e),
            "elapsed": elapsed
        }


def print_separator():
    """Affiche une ligne de séparation."""
    print(f"{Colors.OKCYAN}{'='*80}{Colors.ENDC}")


def run_all_tests(yaml_path: Path, api_url: str = "http://localhost:8000/api/chat",
                  web_search: bool = True, delay: float = 1.0):
    """
    Lance tous les tests depuis le fichier YAML.
    
    Args:
        yaml_path: Chemin vers test_queries.yaml
        api_url: URL de l'API
        web_search: Active recherche web (plus lent, actif par défaut)
        delay: Délai entre requêtes (secondes)
    """
    print(f"\n{Colors.HEADER}{Colors.BOLD}🧪 YanaChat Test Suite{Colors.ENDC}")
    print(f"{Colors.OKBLUE}📁 Fichier: {yaml_path}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}🌐 API: {api_url}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}🔍 Web Search: {'✅ Activé' if web_search else '❌ Désactivé'}{Colors.ENDC}")
    print()
    
    # Charger queries
    queries = load_queries(yaml_path)
    print(f"{Colors.OKGREEN}📝 {len(queries)} queries chargées{Colors.ENDC}\n")
    
    # Stats
    total = len(queries)
    success_count = 0
    error_count = 0
    timeout_count = 0
    total_time = 0.0
    
    # Session ID unique pour tous les tests (mémoire conversation)
    session_id = f"test_session_{int(time.time())}"
    
    # Exécuter chaque query
    for i, query in enumerate(queries, 1):
        print_separator()
        print(f"{Colors.BOLD}[{i}/{total}] Query:{Colors.ENDC}")
        print(f"  {Colors.OKCYAN}{query}{Colors.ENDC}")
        print()
        
        result = test_query(query, api_url, web_search, session_id)
        total_time += result["elapsed"]
        
        if result["status"] == "success":
            success_count += 1
            print(f"{Colors.OKGREEN}✅ SUCCESS ({result['elapsed']:.2f}s){Colors.ENDC}")
            print(f"\n{Colors.BOLD}Réponse:{Colors.ENDC}")
            # Limiter affichage à 500 caractères pour lisibilité
            response_text = result["response"]
            if len(response_text) > 500:
                print(f"  {response_text[:500]}...")
                print(f"  {Colors.WARNING}[Réponse tronquée, {len(response_text)} caractères total]{Colors.ENDC}")
            else:
                print(f"  {response_text}")
        
        elif result["status"] == "timeout":
            timeout_count += 1
            print(f"{Colors.WARNING}⏱️  TIMEOUT ({result['elapsed']:.2f}s){Colors.ENDC}")
            print(f"  {result['error']}")
        
        else:  # error
            error_count += 1
            print(f"{Colors.FAIL}❌ ERROR ({result['elapsed']:.2f}s){Colors.ENDC}")
            print(f"  {result['error']}")
        
        print()
        
        # Délai entre requêtes (sauf dernière)
        if i < total and delay > 0:
            time.sleep(delay)
    
    # Résumé final
    print_separator()
    print(f"\n{Colors.HEADER}{Colors.BOLD}📊 RÉSUMÉ DES TESTS{Colors.ENDC}\n")
    print(f"  Total queries:    {total}")
    print(f"  {Colors.OKGREEN}✅ Succès:         {success_count}{Colors.ENDC}")
    print(f"  {Colors.FAIL}❌ Erreurs:        {error_count}{Colors.ENDC}")
    print(f"  {Colors.WARNING}⏱️  Timeouts:       {timeout_count}{Colors.ENDC}")
    print(f"  ⏱️  Temps total:     {total_time:.2f}s")
    print(f"  📈 Temps moyen:     {total_time/total:.2f}s/query")
    print()
    
    # Taux de réussite
    success_rate = (success_count / total * 100) if total > 0 else 0
    if success_rate == 100:
        print(f"{Colors.OKGREEN}{Colors.BOLD}🎉 100% de réussite !{Colors.ENDC}")
    elif success_rate >= 80:
        print(f"{Colors.OKGREEN}✅ {success_rate:.1f}% de réussite{Colors.ENDC}")
    elif success_rate >= 50:
        print(f"{Colors.WARNING}⚠️  {success_rate:.1f}% de réussite{Colors.ENDC}")
    else:
        print(f"{Colors.FAIL}❌ {success_rate:.1f}% de réussite{Colors.ENDC}")
    
    print()
    return success_count, error_count, timeout_count


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test YanaChat avec queries YAML")
    parser.add_argument(
        "--yaml",
        default="tests/test_queries.yaml",
        help="Chemin vers fichier YAML (défaut: tests/test_queries.yaml)"
    )
    parser.add_argument(
        "--api",
        default="http://localhost:8000/api/chat",
        help="URL de l'API (défaut: http://localhost:8000/api/chat)"
    )
    parser.add_argument(
        "--no-web-search",
        action="store_false",
        dest="web_search",
        help="Désactive recherche web (activée par défaut)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Délai entre requêtes en secondes (défaut: 2.0, min recommandé pour web_search)"
    )
    
    args = parser.parse_args()
    
    # Vérifier que fichier YAML existe
    yaml_path = Path(args.yaml)
    if not yaml_path.exists():
        print(f"{Colors.FAIL}❌ Fichier introuvable: {yaml_path}{Colors.ENDC}")
        sys.exit(1)
    
    # Vérifier que l'API est accessible
    try:
        health_url = args.api.replace("/api/chat", "/health")
        response = requests.get(health_url, timeout=5)
        if response.status_code != 200:
            print(f"{Colors.WARNING}⚠️  API health check failed: {response.status_code}{Colors.ENDC}")
            print("Vérifiez que le serveur est lancé (uvicorn app.main:app)")
            sys.exit(1)
    except Exception as e:
        print(f"{Colors.FAIL}❌ Impossible de contacter l'API: {e}{Colors.ENDC}")
        print("Vérifiez que le serveur est lancé (uvicorn app.main:app)")
        sys.exit(1)
    
    # Lancer tests
    success, errors, timeouts = run_all_tests(
        yaml_path=yaml_path,
        api_url=args.api,
        web_search=args.web_search,
        delay=args.delay
    )
    
    # Exit code basé sur résultats
    if errors > 0 or timeouts > 0:
        sys.exit(1)
    else:
        sys.exit(0)
