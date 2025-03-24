'''
Les paramètres des models.
'''

NB_NEURONES = 800 #         M1 : 200    | M2 : 200    | M3 : 200    | M6 : 200    | M7 : 200    | M8 : 400      | M9 : 400      | M10 : 800     | M11 : 800     | M12 : 800
NB_COUCHES = 1 #            M1 : 1      | M2 : 1      | M3 : 1      | M6 : 1      | M7 : 1      | M8 : 1        | M9 : 1        | M10 : 1       | M11 : 1       | M12 : 1
LEARNING_RATE = 0.001 #     M1 : 0.001  | M2 : 0.001  | M3 : 0.001  | M6 : 0.001  | M7 : 0.001  | M8 : 0.001    | M9 : 0.001    | M10 : 0.001   | M11 : 0.001   | M12 : 0.001
# optimizer                 M1 : ADAM   | M2 : ADAM   | M3 : ADAM   | M6 : ADAM   | M7 : ADAM   | M8 : ADAM     | M9 : ADAM     | M10 : ADAM    | M11 : ADAM    | M12 : ADAM
# loss                      M1 : MSE    | M2 : MSE    | M3 : MSE    | M6 : MSE    | M7 : MSE    | M8 : MSE      | M9 : MSE      | M10 : MSE     | M11 : MSE     | M12 : MSE
BATCH_SIZE = 55 #           M1 : 80     | M2 : 55     | M3 : 55     | M6 : 55     | M7 : 55     | M8 : 55       | M9 : 55       | M10 : 55      | M11 : 55      | M12 : 65
STEP_PER_EPOCH = 100 #      M1 : 1000   | M2 : 1000   | M3 : 100    | M6 : 100    | M7 : 100    | M8 : 100      | M9 : 100      | M10 : 100     | M11 : 100     | M12 : 100
EPOCH = 1000 #              M1 : 10     | M2 : 20     | M3 : 200    | M6 : 100    | M7 : 200    | M8 : 200      | M9 : 1000     | M10 : 1000    | M11 : 1000    | M12 : 1000
# WinState used             M1 : Yes    | M2 : Yes    | M3 : Yes    | M6 : No     | M7 : No     | M8 : Yes      | M9 : Yes      | M10 : No      | M11 : Yes     | M12 : Yes
# Inverted WinState team    M1 : No     | M2 : No     | M3 : No     | M6 : No     | M7 : No     | M8 : No       | M9 : No       | M10 : No      | M11 : No      | M12 : Yes
# Human game examples       M1 : No     | M2 : No     | M3 : No     | M6 : No     | M7 : No     | M8 : No       | M9 : No       | M10 : No      | M11 : No      | M12 : No

INFOS_ALL_MODELS = {
    1: ('~ 21-11-2024', 'BASE'),
    2: ('~ 21-11-2024', 'batch size 55 (-) | epoch 20 (+)'),
    3: ('~ 21-11-1014', 'epoch 200 (+) | step per epoch 100 (-)'),
    4: ('~ 26-11-2024', 'N/A'),
    5: ('~ 26-11-2024', 'N/A'),
    6: ('~ 26-11-2024', 'epoch 100 (-) | WinState used False'),
    7: ('~ 26-11-2024', 'epoch 200 (+)'),
    8: ('27-11-2024', 'nb neurones 400 (+) | WinState used True'),
    9: ('27-11-2024', 'epoch 1000 (+)'),
    10: ('10-12-2024', 'nb neurones 800 (+) | Winstate used False'),
    11: ('16-12-2024', 'Winstate used True\ncurrently BEST'),
    12: ('16-12-2024', 'Inverted WinState team True'),
    13: ('13-01-2025', 'Identique à modèle 12 (erreur)'),
    14: ('18-01-2025', 'MultipleWinAndLoss activated')
}

def date_model(NUM_MODEL):
    """cherche pas, c'est une constante fonction"""
    return INFOS_ALL_MODELS[NUM_MODEL][0]

def changes_model(NUM_MODEL):
    """cherche pas, c'est une constante fonction"""
    return INFOS_ALL_MODELS[NUM_MODEL][1]