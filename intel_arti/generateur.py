from random import randint, sample
from numpy import reshape, array
from cube_environement import CubeEnv
from agent_class import DQNAgent
from copy import deepcopy

environnement = CubeEnv()
agent = DQNAgent(state_size=54, action_size=27)
model_name = "dqn_test_model_"

cases = (0, 1, 2)
nb_session = 50

CORRESP = (
    ((2, 4), (1, 3)),
    ((2, 4), (0, 5)),
    ((0, 5), (1, 3)),
    ((2, 4), (0, 5)),
    ((0, 5), (1, 3)),
    ((2, 4), (1, 3))
)

def get_position(position : list[int, int, int], sens: int) -> tuple[int, int, int]:
    face, ligne, colonne = position
    if sens == 2 : sens = randint(0, 1)
    sec_face = CORRESP[face][sens][randint(0, 1)]
    if not(face and sec_face) or ligne == colonne == 1 :
        return sec_face, ligne, colonne
    if not 5 in (face, sec_face) :
        if 4 in (sec_face, face) :
            if not 3 in (sec_face, face) :
                face = 0 if face == 4 else face
                sec_face = 0 if sec_face == 4 else sec_face
        sens_tour = face - sec_face
        if sens_tour == 1 : # Sens horaire
            if ligne == 0 :
                ligne += colonne
                colonne = 2
                return sec_face, ligne, colonne
            if colonne == 0 :
                colonne += 2 - ligne
                ligne = 0
                return sec_face, ligne, colonne
            if ligne == 2 :
                ligne -= colonne
                colonne = 2
                return sec_face, ligne, colonne
            if colonne == 2 :
                colonne -= ligne
                ligne = 2
                return sec_face, ligne, colonne
        else : # Sens anti-horaire
            if ligne == 0 :
                ligne += 2 - colonne
                colonne = 0
                return sec_face, ligne, colonne
            if colonne == 0 :
                colonne += 2 - ligne
                ligne = 2
                return sec_face, ligne, colonne
            if ligne == 2 :
                ligne -= colonne
                colonne = 2
                return sec_face, ligne, colonne
            if colonne == 2 :
                colonne -= ligne
                ligne = 2
                return sec_face, ligne, colonne
    else :
        if 1 in (face, sec_face) or 3 in (face, sec_face) :
            return sec_face, ligne, colonne
        else :
            ligne = 2 - ligne
            colonne = 2 - colonne
            return sec_face, ligne, colonne




def creer_etat(face : int) :
    sens = randint(0, 2)
    duo = sample(cases, 2)
    if sens == 0 : # Horizontal
        numero = randint(0, 2)
        environnement.cube.faces[face][numero][duo[0]] = environnement.cube.faces[face][numero][duo[1]] = 1
        position2 = face, numero, duo[0]
        position3 = face, numero, duo[1]
        position1 = (face, numero, [i for i in range(3) if i not in duo][0])
    elif sens == 1 : # Vertical
        numero = randint(0, 2)
        environnement.cube.faces[face][duo[0]][numero] = environnement.cube.faces[face][duo[1]][numero] = 1
        position2 = face, duo[0], numero
        position3 = face, duo[1], numero
        position1 = (face, [i for i in range(3) if i not in duo][0], numero)
    else : # Diagonal
        numero = randint(0, 1)
        if numero :
            environnement.cube.faces[face][duo[0]][2-duo[0]] = environnement.cube.faces[face][duo[1]][2-duo[1]] = 1
            position2 = face, duo[0], 2 - duo[0]
            position3 = face, duo[1], 2 - duo[1]
            nb = [i for i in range(3) if i not in duo][0]
            position1 = (face, nb, 2-nb)
        else :
            environnement.cube.faces[face][duo[0]][duo[0]] = environnement.cube.faces[face][duo[1]][duo[1]] = 1
            position2 = face, duo[0], duo[0]
            position3 = face, duo[1], duo[1]
            nb = [i for i in range(3) if i not in duo][0]
            position1 = (face, nb, nb)
    if face != 0 :
        position1 = get_position(position1, sens)
        environnement.cube.faces[position1[0]][position1[1]][2] = 1

    else :
        not_normal = randint(0, 1)
        if not_normal :
            position1 = get_position(position1, sens)
            environnement.cube.faces[position1[0]][position1[1]][2] = 1
        
    croix = randint(0, 5)
    ronds = randint(0, 7)
    for _ in range(croix) :
        face = randint(0, 5)
        ligne = randint(0, 2)
        colonne = randint(0, 2)
        if not environnement.cube.faces[face][ligne][colonne] and (face, ligne, colonne) not in (position1, position2, position3):
            environnement.cube.faces[face][ligne][colonne] = 1
    for _ in range(ronds) :
        face = randint(0, 5)
        ligne = randint(0, 2)
        colonne = randint(0, 2)
        if not environnement.cube.faces[face][ligne][colonne] and (face, ligne, colonne) not in (position1, position2, position3):
            environnement.cube.faces[face][ligne][colonne] = -1

def entrainement_clos(face : int) :
    creer_etat(face)
    while environnement.check_done()[0] :
        print("zut")
        environnement.reset()
        creer_etat(face)
    cube = deepcopy(environnement.cube.faces)
    state = reshape(array(cube).flatten(), (1, 54))
    illegal_moves = [i + 18 for i in range(9) if state[0][i]]
    actions = [i for i in range(27)]
    action = agent.act(state, illegal_moves, test_model=True)
    actions.remove(action)
    for i in range(27) :
        done, reward = environnement.single_step(action)
        if done :
            if reward > 0 :
                target = agent.model.predict(state, verbose=0)
                target[0][action] = 1_000
                agent.model.fit(state, target, epochs=1, verbose=0)
                return int(i == 0)
            elif reward < 0 :
                print(state)
                target = agent.model.predict(state, verbose=0)
                target[0][action] = -100
                agent.model.fit(state, target, epochs=1, verbose=0)
            else :
                print("Draw")
                target = agent.model.predict(state, verbose=0)
                target[0][action] = -10
                agent.model.fit(state, target, epochs=1, verbose=0)
        else :
            target = agent.model.predict(state, verbose=0)
            target[0][action] = 0
            agent.model.fit(state, target, epochs=1, verbose=0)
            environnement.cube.faces = deepcopy(cube)
        if i != 26 :
            action = actions.pop(randint(0, len(actions) - 1))
    print(f"Probleme {face}")
    print(state)
    return 0

for session in range(nb_session) :
    succes = 0
    for i in range(12) :
        succes += entrainement_clos(i%6)
        environnement.reset()
    print(f"Session {session} :", succes, "/12")
    model_path = model_name + str(session + 1) +  ".keras"
    agent.model.save(model_path)