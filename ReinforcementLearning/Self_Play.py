import ReinforcementLearning.ChessAI as AI
import chess
import copy
import Support.FenLoad as FL
import os
import shutil
import tensorflow as tf
import objgraph
from Support.Record import GameInfo
# import ChessBoard


class Play:
    def __init__(self):
        self.gameInfo = GameInfo()
        g = tf.Graph()
        postCheckpointPath = '../Checkpoint/Later/'
        preCheckpointPath = '../Checkpoint/Former/'
        self.LaterAI = AI.ChessAI(postCheckpointPath)
        self.FormerAI = AI.ChessAI(preCheckpointPath)
        self.loadFenData= FL.FenLoad()
        self.gameInfo.load()
        self.LIMITofCOUNT = 1000
    def __del__(self):
        print("")

    def saveRLData(self, chessBoard, result):
        # 파일 경로에 주어진 data를 저장
        datas = []

        try:
            f = open('../Data/RLData.txt', 'a')
        except:
            f = open('../Data/RLData.txt', 'w')

        while len(chessBoard.move_stack) != 0:
            command = chessBoard.pop().__str__()
            fen = chessBoard.fen()

            datas.append(fen + ":" + command + ":" + result)

        copyDatas = copy.deepcopy(datas)

        for i in range(len(datas)):
            # 데이터를 역순으로 저장
            data = datas.pop() + "\n"
            f.write(data)

        f.close()

        return copyDatas

    def reinforcementLearning(self, fenDatas, turn):
        input,rolloutInput, label, result = self.loadFenData.getDataForRL(fenDatas)
        self.LaterAI.learning(input,rolloutInput, label, result)

    def resettingPastPolicy(self):
        postPolicyFilePath = self.LaterAI.getNetwork().getFilePath()
        prePolicyFilePath = self.FormerAI.getNetwork().getFilePath()

        currentPolicyFileLists = os.listdir(postPolicyFilePath)

        # 학습된 체크포인트 파일을 pastPolicy디렉터리로 이동
        for filename in currentPolicyFileLists:
            previousPath = os.path.join(postPolicyFilePath, filename)
            afterPath = os.path.join(prePolicyFilePath, filename)
            shutil.copy(previousPath, afterPath)

        self.FormerAI.getNetwork().restoreCheckpoint()
    def moveFile(self,fromPath, toPath):
        fromPathFileList = os.listdir(fromPath)

        for filename in fromPathFileList:
            prePath = os.path.join(fromPath, filename)
            afterPath = os.path.join(toPath, filename)
            shutil.copy(prePath, afterPath)

    def resettingCheckpoint(self):
        # Moving Policy checkpoint
        fromPath = self.LaterAI.networks.getPolicyNetwork().getFilePath()
        toPath = self.FormerAI.networks.getPolicyNetwork().getFilePath()
        self.moveFile(fromPath,toPath)

        # Moving Value Checkpoint
        fromPath = self.LaterAI.networks.getValueNetwork().getFilePath()
        toPath = self.FormerAI.networks.getValueNetwork().getFilePath()
        self.moveFile(fromPath, toPath)

        # Moving Rollout checkpoint
        fromPath = self.LaterAI.networks.getRollout().getFilePath()
        toPath = self.FormerAI.networks.getRollout().getFilePath()
        self.moveFile(fromPath, toPath)


    def playChessForReinforcementLearning(self, num):
        # 펜데이터로 경기가 끝날때 까지 진행
        chessBoard = chess.Board()
        turn=None

        if num % 2 == 0:
            white = self.FormerAI
            black = self.LaterAI
            turn=False
        else:
            white = self.LaterAI
            black = self.FormerAI
            turn =True
        gameCount = 0
        # for i in range(1000000000):
        #     pass

        while not chessBoard.is_game_over():
            objgraph.show_most_common_types()


            # print(self.gameInfo.info)
            # print(type(self.gameInfo.info))
            if gameCount >self.LIMITofCOUNT:
                break
            print("---------------")
            if chessBoard.turn:
                print("White Turn")
            else:
                print("Black Turn")
            print("a b c d e f g h")
            print("---------------")
            print(chessBoard, chr(13))
            print("---------------")
            print("a b c d e f g h")
            if chessBoard.turn:
                move = white.get_MCTS(chessBoard)
                # print("백: ", move)#, ", score: ", score)
            else:
                move = black.get_MCTS(chessBoard)
                # print("흑: ", move)#, ", score: ", score)
            chessBoard.push(chess.Move.from_uci(move))
            gameCount += 1

        if gameCount>self.LIMITofCOUNT:
            result = '1/2-1/2'
        else:
            result = chessBoard.result()

        if num % 2 == 0: #Later 흑, Former 백

            if result =='0-1': #Later Black 승
               self.gameInfo.info['CurrentLaterBlackWin']+=1
               self.gameInfo.info['LaterBlackWin']+=1
               self.gameInfo.info['LaterWin']+=1
               str = "LaterAi Win, Self-Play Result: " + result
            elif result =='1-0': #Later Black 패
                self.gameInfo.info['CurrentFormerWhiteWin'] += 1
                self.gameInfo.info['FormerWhiteWin']+=1
                self.gameInfo.info['FormerWin']+=1
                str = "LaterAi Lose, Self-Play Result: " + result
            else:
                str = "LaterAi Draw, Self-Play Result: " + result
        else: # Later 백, Former 흑
            if result == '1-0':  # Later White 승
                self.gameInfo.info['CurrentLaterWhiteWin'] += 1
                self.gameInfo.info['LaterWhiteWin']+=1
                self.gameInfo.info['LaterWin']+=1
                str = "LaterAi Win, Self-Play Result: " + result
            elif result =='0-1': # Later White 패
                self.gameInfo.info['CurrentFormerBlackWin'] +=1
                self.gameInfo.info['FormerBlackWin']+=1
                self.gameInfo.info['FormerWin']+=1
                str = "LaterAi Lose, Self-Play Result: " + result
            else:
                str = "LaterAi Lose, Self-Play Result: " + result

        self.gameInfo.info['CurrentGameCount']+=1
        self.gameInfo.info['GameCount']+=1
        print(str)

        with open('Self-PlayResult.txt', 'a') as f:
            f.write(str + "\n")

        # 게임이 끝났을 때 체스 데이터를 저장
        fenDatas = self.saveRLData(chessBoard, result)
        self.reinforcementLearning(fenDatas,turn)

        #Game Info를 Json으로 저장
        self.gameInfo.save()
        isChange = self.gameInfo.is_ChangeCheckpoint()
        return isChange

    def fixResult(self, turn, result):
        if result == "1/2-1/2":
            return "draw"
        if turn:
            if result == "1-0":
                return "RL_Policy Win!"
            else:
                return "RL_Policy Lose!"
        else:
            if result == "1-0":
                return "RL_Policy Lose!"
            else:
                return "RL_Policy Win!"

if __name__ == '__main__':


    count = 0
    while True:
        sp = Play()
        isChange = sp.playChessForReinforcementLearning(count)
        count +=1

        if isChange:
            sp.resettingPastPolicy()
            sp.gameInfo.upRotaionCount()
            with open('../File/Self-PlayResult.txt', 'a') as f:
                f.write("-----------Change Checkpoint------------\n")
        del sp
