'''
Les paramètres des models.
'''

# Best                                                      BEST

NB_NEURONES = 200 #         M1 : 200    | M2 : 200      | M3 : 200      | M6 : 200      | M7 : 200  
NB_COUCHES = 1 #            M1 : 1      | M2 : 1        | M3 : 1        | M6 : 1        | M7 : 1    
LEARNING_RATE = 0.001 #     M1 : 0.001  | M2 : 0.001    | M3 : 0.001    | M6 : 0.001    | M7 : 0.001
# optimizer                 M1 : ADAM   | M2 : ADAM     | M3 : ADAM     | M6 : ADAM     | M7 : ADAM 
# loss                      M1 : MSE    | M2 : MSE      | M3 : MSE      | M6 : MSE      | M7 : MSE  
BATCH_SIZE = 55 #           M1 : 80     | M2 : 55       | M3 : 55       | M6 : 55       | M7 : 55   
STEP_PER_EPOCH = 100 #      M1 : 1000   | M2 : 1000     | M3 : 100      | M6 : 100      | M7 : 100  
EPOCH = 200 #               M1 : 10     | M2 : 20       | M3 : 200      | M6 : 100      | M7 : 200  
# WinState used             M1 : Yes    | M2 : Yes      | M3 : Yes      | M6 : No       | M7 : No   
# Inverted WinState team    M1 : No     | M2 : No       | M3 : No       | M6 : No       | M7 : No   
# Human game examples       M1 : No     | M2 : No       | M3 : No       | M6 : No       | M7 : No   