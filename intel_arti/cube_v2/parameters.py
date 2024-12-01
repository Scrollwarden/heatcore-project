'''
Les paramètres des models.
'''

# Best                                                      BEST

NB_NEURONES = 200 #         M1 : 200    | M2 : 200    | M3 : 200    | M6 : 200    | M7 : 200    | M8 : 400      | M9 : 400
NB_COUCHES = 1 #            M1 : 1      | M2 : 1      | M3 : 1      | M6 : 1      | M7 : 1      | M8 : 1        | M9 : 1
LEARNING_RATE = 0.001 #     M1 : 0.001  | M2 : 0.001  | M3 : 0.001  | M6 : 0.001  | M7 : 0.001  | M8 : 0.001    | M9 : 0.001
# optimizer                 M1 : ADAM   | M2 : ADAM   | M3 : ADAM   | M6 : ADAM   | M7 : ADAM   | M8 : ADAM     | M9 : ADAM
# loss                      M1 : MSE    | M2 : MSE    | M3 : MSE    | M6 : MSE    | M7 : MSE    | M8 : MSE      | M9 : MSE
BATCH_SIZE = 55 #           M1 : 80     | M2 : 55     | M3 : 55     | M6 : 55     | M7 : 55     | M8 : 55       | M9 : 55
STEP_PER_EPOCH = 100 #      M1 : 1000   | M2 : 1000   | M3 : 100    | M6 : 100    | M7 : 100    | M8 : 100      | M9 : 100
EPOCH = 200 #               M1 : 10     | M2 : 20     | M3 : 200    | M6 : 100    | M7 : 200    | M8 : 200      | M9 : 1000
# WinState used             M1 : Yes    | M2 : Yes    | M3 : Yes    | M6 : No     | M7 : No     | M8 : Yes      | M9 : Yes
# Inverted WinState team    M1 : No     | M2 : No     | M3 : No     | M6 : No     | M7 : No     | M8 : No       | M9 : No
# Human game examples       M1 : No     | M2 : No     | M3 : No     | M6 : No     | M7 : No     | M8 : No       | M9 : No

# M7 : Ne joue pas de pions pendant un long moment
# M1, M2, M3 : jouent sur la première case, pas difficiles à vaincre
# M4 : Joue directement au centre.
# M5 : Ne joue pas de pions pendant un long moment.
# M6 : se fait battre en morpion simple hyper facilement. Ne pose pas de pion au premier coup mais joue directement après.
# M8


# "Normal" players  Strange players (no pawns at beginning)     MAIN CLASSMENT
# #1 : M9           #1 : M8                                     #1 : M9
# #2 : M4           #2 : M7                                     #2 : M4
# #3 : M3           #3 : M5                                     #3 : M8
# #4 : M2                                                       #4 : M7
# #5 : M1                                                       #5 : M5
# #6 : M6                                                       #6 : M3
#                                                               #7 : M2
#                                                               #8 : M1
#                                                               #9 : M6

# 200 epoch seem good
# WinState seem to ensure model to use pawns at beginning

INFOS_ALL_MODELS = {
    1: ('~ 21-11-2024', 'BASE'),
    2: ('~ 21-11-2024', 'batch size 55 (-) | epoch 20 (+)'),
    3: ('~ 21-11-1014', 'epoch 200 (+) | step per epoch 100 (-)'),
    4: ('~ 26-11-2024', 'N/A'),
    5: ('~ 26-11-2024', 'N/A'),
    6: ('~ 26-11-2024', 'epoch 100 (-) | WinState used False'),
    7: ('~ 26-11-2024', 'epoch 200 (+)'),
    8: ('27-11-2024', 'nb neurones 400 (+) | WinState used True'),
    9: ('27-11-2024', 'epoch 1000 (+)')
}

def date_model(NUM_MODEL):
    """cherche pas, c'est une constante fonction"""
    return INFOS_ALL_MODELS[NUM_MODEL][0]

def changes_model(NUM_MODEL):
    """cherche pas, c'est une constante fonction"""
    return INFOS_ALL_MODELS[NUM_MODEL][1]