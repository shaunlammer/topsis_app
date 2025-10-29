import numpy as np

matriz = np.array([
    [90, 90, 85, 90, 100, 90],  # A
    [75, 85, 60, 75, 85, 85],   # B
    [65, 82, 45, 60, 70, 65]    # C
], dtype=float)


pesos = np.array([0.23, 0.09, 0.15, 0.09, 0.30, 0.14])


tipos = ['max', 'max', 'max', 'min', 'max', 'min']


denominadores = np.sqrt(np.sum(matriz**2, axis=0))
matriz_norm = matriz / denominadores


matriz_pond = matriz_norm * pesos


ideal_pos = np.array([
    np.max(matriz_pond[:, j]) if tipos[j] == 'max' else np.min(matriz_pond[:, j])
    for j in range(len(tipos))
])
ideal_neg = np.array([
    np.min(matriz_pond[:, j]) if tipos[j] == 'max' else np.max(matriz_pond[:, j])
    for j in range(len(tipos))
])


dist_pos = np.sqrt(np.sum((matriz_pond - ideal_pos)**2, axis=1))
dist_neg = np.sqrt(np.sum((matriz_pond - ideal_neg)**2, axis=1))


coeficientes = dist_neg / (dist_pos + dist_neg)

ranking = np.argsort(-coeficientes)


alternativas = ['A', 'B', 'C']
print("Ranking TOPSIS:")
for i in ranking:
    print(f"{alternativas[i]} → Coeficiente: {round(coeficientes[i], 4)}")