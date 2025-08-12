# scripts/automation.py

def modifier_fichier():
    chemin = "server.py"  # Chemin relatif depuis la racine du projet
    try:
        with open(chemin, "r", encoding="utf-8") as f:
            contenu = f.read()

        # Exemple : remplacer un mot ou une phrase dans le code
        nouveau_contenu = contenu.replace("print('Hello')", "print('Hello from automation!')")

        with open(chemin, "w", encoding="utf-8") as f:
            f.write(nouveau_contenu)

        print(f"Fichier {chemin} modifié avec succès.")
    except FileNotFoundError:
        print(f"Le fichier {chemin} n'a pas été trouvé.")
    except Exception as e:
        print(f"Erreur lors de la modification du fichier : {e}")


if __name__ == "__main__":
    modifier_fichier()
