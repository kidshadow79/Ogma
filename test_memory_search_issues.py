"""
Test de diagnostic des problèmes de recherche mémoire OGMA
"""

import re

# Simuler la logique d'expansion et nettoyage
def _expand_personal_pronouns_test(query_text, user_name='Yohan'):
    """Test de la fonction d'expansion des pronoms personnels"""
    expanded_query = query_text.lower()
    
    pronoun_patterns = [
        (r'\b(mon|ma|mes)\s+([a-zA-Zàâäéèêëïîôöùûüÿç]+)', rf'\2 de {user_name}'),
        (r'\bde\s+moi\b', f'de {user_name}'),
        (r'\bje\s+suis\b', f'{user_name} est'),
        (r"j'ai\b", f'{user_name} a'),
        (r'\bje\s+([a-zA-Zàâäéèêëïîôöùûüÿç]+)', rf'{user_name} \1'),
    ]
    
    changes = []
    for pattern, replacement in pronoun_patterns:
        before = expanded_query
        expanded_query = re.sub(pattern, replacement, expanded_query, flags=re.IGNORECASE)
        if before != expanded_query:
            changes.append(f"  Expansion: '{before}' → '{expanded_query}'")
    
    return expanded_query, changes

def _extract_keywords_test(query):
    """Test de la fonction d'extraction des mots-clés"""
    stopwords = {
        'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'l',
        'et', 'ou', 'mais', 'donc', 'or', 'ni', 'car',
        'je', 'tu', 'il', 'elle', 'nous', 'vous', 'ils', 'elles',
        'me', 'te', 'se', 'ce', 'ça',
        'mon', 'ma', 'mes', 'ton', 'ta', 'tes', 'son', 'sa', 'ses',
        'qui', 'que', 'quoi', 'dont', 'où',
        'est', 'es', 'suis', 'sommes', 'êtes', 'sont',
        'quelle', 'quelles', 'quel', 'quels',
        'dans', 'sur', 'sous', 'avec', 'sans', 'pour', 'par', 'vers', 'chez',
        'salut', 'bonjour', 'bonsoir', 'coucou', 'hey', 'yo',
        'bien', 'très', 'trop', 'peu', 'assez', 'plus', 'moins',
        'y', 'en', 'ne', 'pas', 'non', 'oui', 'si'
    }
    
    original_query = query
    query = re.sub(r'[?!;,\.]+', ' ', query)
    words = query.lower().split()
    
    keywords = []
    filtered_words = []
    for word in words:
        clean_word = word.strip()
        if (clean_word not in stopwords or
            '-' in clean_word or
            len(clean_word) > 8):
            keywords.append(clean_word)
        else:
            filtered_words.append(clean_word)
    
    cleaned = ' '.join(keywords)
    if len(keywords) < 2:
        return original_query, f"Trop peu de mots-clés ({len(keywords)}), requête originale conservée"
    
    analysis = f"Mots conservés: {keywords}, Mots filtrés: {filtered_words}"
    return cleaned, analysis

def test_query_processing():
    """Test des requêtes problématiques identifiées par l'utilisateur"""
    
    test_queries = [
        'taille',
        'ma taille', 
        'quelle est ma taille',
        'légende des 2 phares',
        'genèse des 2 phares',
        'légende phares',
        'genèse phares',
        'les deux phares',
        'histoire des phares'
    ]
    
    print("🔍 DIAGNOSTIC RECHERCHE MÉMOIRE OGMA")
    print("=" * 60)
    print("Test du pipeline de traitement des requêtes:")
    print("1. Expansion des pronoms personnels")
    print("2. Extraction des mots-clés (suppression stopwords)")
    print("")
    
    for i, query in enumerate(test_queries, 1):
        print(f"📝 TEST {i}: '{query}'")
        
        # Étape 1: Expansion des pronoms
        expanded, changes = _expand_personal_pronouns_test(query)
        if changes:
            for change in changes:
                print(change)
        else:
            print("  Aucune expansion nécessaire")
        
        # Étape 2: Extraction des mots-clés
        cleaned, analysis = _extract_keywords_test(expanded)
        print(f"  Mots-clés: '{cleaned}'")
        print(f"  Analyse: {analysis}")
        
        # Diagnostic
        if cleaned != query.lower():
            print(f"  🔄 TRANSFORMATION: '{query}' → '{cleaned}'")
        else:
            print(f"  ✅ REQUÊTE INCHANGÉE")
        
        print("")

def analyze_search_issues():
    """Analyse des problèmes spécifiques mentionnés"""
    
    print("🚨 ANALYSE DES PROBLÈMES SPÉCIFIQUES")
    print("=" * 60)
    
    issues = [
        {
            'problème': 'Taille non trouvée',
            'requête_utilisateur': 'ma taille', 
            'description': 'L\'IA n\'a pas su répondre sur la taille alors que le souvenir existe'
        },
        {
            'problème': 'Légende des 2 phares non trouvée',
            'requête_utilisateur': 'légende des 2 phares',
            'description': 'N\'a pas trouvé avec "légende" mais trouvé avec "genèse"'
        }
    ]
    
    for issue in issues:
        print(f"🔴 PROBLÈME: {issue['problème']}")
        print(f"   Requête: '{issue['requête_utilisateur']}'")
        print(f"   Description: {issue['description']}")
        
        # Simuler le pipeline
        expanded, _ = _expand_personal_pronouns_test(issue['requête_utilisateur'])
        cleaned, _ = _extract_keywords_test(expanded)
        
        print(f"   Pipeline OGMA: '{issue['requête_utilisateur']}' → '{expanded}' → '{cleaned}'")
        print(f"   🤔 HYPOTHÈSE: Le souvenir contient-il les mots '{cleaned}' ?")
        print("")

def similarity_threshold_analysis():
    """Analyse des seuils de similarité"""
    
    print("📊 ANALYSE SEUILS DE SIMILARITÉ")
    print("=" * 60)
    print("Seuils actuels dans le code:")
    print("- search_memories(): threshold=0.3 (seuil de base)")
    print("- retrieve_mixed_context(): k=12 souvenirs récupérés")
    print("- Tri par: 1) impact_score, 2) similarity_score")
    print("")
    print("🤔 PROBLÈMES POTENTIELS:")
    print("1. Seuil 0.3 peut être trop élevé pour certains termes")
    print("2. Les mots-clés extraits peuvent ne pas correspondre au vocabulaire des souvenirs")
    print("3. L'embedding peut ne pas capturer correctement les synonymes")
    print("4. Les souvenirs peuvent utiliser une terminologie différente")

if __name__ == "__main__":
    test_query_processing()
    analyze_search_issues() 
    similarity_threshold_analysis()