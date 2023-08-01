title: Tiny Chessbot
date: TODO
author: Jim Barrett
post_id: 10

There's a YouTuber who I've been following some time called [SebastianLague](https://www.youtube.com/@SebastianLague). He makes really great content aroud coding, particularly of games. I came to his channel via a video he made on writing a chess engine, and he recently [announced a competition](https://www.youtube.com/watch?v=iScy18pVR58). The challenge is to write a chess engine, but with a restricted amount of real estate with which to write the code. I thought this sounded like it could be fun, so I downloaded and setup the competition repo.

He encourages both serious and silly submissions, so I thought I'd go for somewhere in between. The name of my bot is going to be Ms Norbury, because it's a pusher. It pushes pawns.

<div style="width:100%;height:0;padding-bottom:60%;position:relative;"><iframe src="https://giphy.com/embed/pquWIaHkwntJu" width="100%" height="100%" style="position:absolute" frameBorder="0" class="giphy-embed" allowFullScreen></iframe></div><p><a href="https://giphy.com/gifs/pink-mexico-korea-pquWIaHkwntJu">via GIPHY</a></p>

The concept is going to be that the bot is going to be extremely agressive in pushing pawns. If a pawn push is a viable option, even if it's not the very best option, it will always do it. With this philosophy in mind, I will try and make the bot as strong as possible.

I also want to declare my credentials up front here. I am an OK chess player, but nothing particularly special. I hover around 1700-1800 blitz on [lichess](https://lichess.org/@/jimcube27/perf/blitz) and between 1350-1450 on [chess.com](https://www.chess.com/member/jimjimjimmyjim). I have also never coded anything in C# before, although I have coded in enough languages that I hope this shouldn't be too much of a disadvantage. I do know that pushing too many pawns is genrally considered a bad strategy, so I don't expect my bot to be winning many matches in the actual competition.

So with that said, time to set a baseline from which I can work.

### Bot 0 - The baseline

I want to set a simple baseline from which to start. Nothing fancy, but something which honours Ms Norbury's philosphy and isn't completely dumb. The bot comprised 3 pieces;

#### The position evaluation function

I wrote the dumbest sensible evaluation function I could think of. It simply counts the collective score of all the pieces according to the classical "points system" used in chess.

<pre><code class='language-cs'>
private double EvaluatePosition(Board board) {

        if (board.IsInCheckmate()) return (
            board.IsWhiteToMove 
            ? double.NegativeInfinity 
            : double.PositiveInfinity
        );

        Dictionary<PieceType, double> pieceValues = new Dictionary<PieceType, double>();
        pieceValues[PieceType.Pawn] = 1.0;
        pieceValues[PieceType.Knight] = 3.0;
        pieceValues[PieceType.Bishop] = 3.0;
        pieceValues[PieceType.Rook] = 5.0;
        pieceValues[PieceType.Queen] = 9.0;
        
        double score = 0.0;

        PieceList[] allPieceList = board.GetAllPieceLists();
        for (int i=0; i < allPieceList.Length; i++) {
            PieceList pieceList = allPieceList[i];
            if (pieceList.TypeOfPieceInList == PieceType.King) continue;
            score += (
                pieceList.Count 
                * (pieceList.IsWhitePieceList ? 1.0 : -1.0) 
                * pieceValues[pieceList.TypeOfPieceInList]
            );
        }
        return score;
    }
</code></pre>

#### The move evaluation function

I spent quite a long time writing and debugging a function which could search to arbitrary move depths, and never quite did manage to get it working. I figured a good way to ultimately debug such a function would be to have a hard coded depth-1 function to compare it against, so that's what I did. I'll experiment with more sophisticated search functions later.

```csharp
private double EvaluateMove(Board board, Move move) {

        double finalEval;

        board.MakeMove(move);

        Move[] legalMoves = board.GetLegalMoves();

        if (board.IsInCheckmate()) finalEval = (
            board.IsWhiteToMove 
            ? double.NegativeInfinity 
            : double.PositiveInfinity
        );

        else if (legalMoves.Length == 0) finalEval = 0;

        else {
            double[] evals = new double[legalMoves.Length];
            for (int i=0; i< legalMoves.Length; i++) {
                board.MakeMove(legalMoves[i]);
                evals[i] = EvaluatePosition(board);
                board.UndoMove(legalMoves[i]);

            }
            finalEval = board.IsWhiteToMove ? evals.Max() : evals.Min();
        }
        
        board.UndoMove(move);

        return finalEval;
    }
```

#### The move function

This is the function provided for the competition. For now it basically does part of the job of the search function, but then always plays a Pawn move if there's one in its top 4 moves. I think I'll be able to do better than this in terms of really living up to the Ms Norbury spirit. But this will do for a baseline.

```csharp
public Move Think(Board board, Timer timer)
    {

        Random rand = new Random();
        Move[] legalMoves = board.GetLegalMoves();
        
        double scoreMultipler = board.IsWhiteToMove ? 1.0 : -1.0;
        double[] evals = new double[legalMoves.Length];
        for (int i=0; i<legalMoves.Length; i++) {
            evals[i] = scoreMultipler * EvaluateMove(board, legalMoves[i]);
        }

        Array.Sort(evals, legalMoves);

        // I'm a pusher
        for (int i=legalMoves.Length - 1; (i>= 0 && i>=legalMoves.Length -4); i--) {
            if (legalMoves[i].MovePieceType == PieceType.Pawn) {
                return legalMoves[i];
            }
        }

        return legalMoves[legalMoves.Length - 1];
    }
```
#### Results

I evaluated against the simple bot provided by the competition. Its strategy is to always capture the most valuable piece it can, otherwise make random moves. Here are the results;

| Result | # |
| --- | --- |
| Wins | 877 |
| Draws | 114 |
| Losses | 9 |  

And the bot uses 411 brain power capacity.

### Bot 1 - A different baseline

I also wanted to try a different approach to the pusher philosophy. I made a small modification to the search function, so that any move involving a pawn (of the bot, not its opponent) is given a boost of 1 to its position eval. I then removed the pawn move in the top 4 stipulation, and it performs a lot better, now using 385 brain capacity.

| Result | # |
| --- | --- |
| Wins | 930 |
| Draws | 70 |
| Losses | 0 | 

Since the bot provided by the competition repo is so weak, I don't know how well I'm going to be able to discern improvements I'm making in my bot. I am therefore opting to make this bot the opponent for future experiments. I'm going to call it the Marymount Prep bot, for the Mathlete's opponents in the movie.

<div style="width:100%;height:0;padding-bottom:56%;position:relative;"><iframe src="https://giphy.com/embed/l2YWo1dSvTwkaiwPm" width="100%" height="100%" style="position:absolute" frameBorder="0" class="giphy-embed" allowFullScreen></iframe></div><p><a href="https://giphy.com/gifs/filmeditor-mean-girls-movie-l2YWo1dSvTwkaiwPm">via GIPHY</a></p>

### Bot 2 - Common Sense Evaluation

There's more to a chess position than the value of the pieces. For the next iteration of the bot I want to take other factors into account. 

From my limited chess experience, I feel like there are different considerations depending on which phase of the game you're in. In the opening, piece development is important. In the endgame, piece activity, and limiting the activity of the openents pieces is important. In the middlegame, its kind of a mixture of both. 

I expect there'll be several iterations of the position evaluation function, so for this first iteration I'm going to just dump down the basics. In this step I really felt my lack of C# experience, since it really feels like there should be more consise ways of writing things, but here are the new bits of code;

```csharp
private int getGamePhase(Board board) {
    // 0 = opening, 1 = middlegame, 2 = endgame
    if (board.PlyCount < 16) return 0;
    else if (board.PlyCount < 60) return 1;
    else return 2;
}

private double scoreKing(Board board, Piece king) {

    double score = 0.0;
    int goodRank = king.IsWhite ? 0 : 7;
    if (getGamePhase(board) < 3) {
        score += Math.Abs(king.Square.Rank - goodRank) == 0 ? 0.1 : -0.5; 
    }
    return score;

}

private double scoreQueen(Board board, Piece queen) {
    return 9.0 + ((1.0/64.0) * BitboardHelper.GetNumberOfSetBits(
        BitboardHelper.GetSliderAttacks(PieceType.Queen, queen.Square, board)
    ));
}

private double scoreRook(Board board, Piece rook) {
    return 5.0 + ((1.0/64.0) * BitboardHelper.GetNumberOfSetBits(
        BitboardHelper.GetSliderAttacks(PieceType.Rook, rook.Square, board)
    ));
}

private double scoreBishop(Board board, Piece bishop) {
    return 3.0 + ((1.0/64.0) * BitboardHelper.GetNumberOfSetBits(
        BitboardHelper.GetSliderAttacks(PieceType.Bishop, bishop.Square, board)
    ));
}

private double scoreKnight(Board board, Piece knight) {
    return 3.0 + ((1.0/64.0) * Math.Abs(knight.Square.Index - 31));
}

private double scorePawn(Board board, Piece pawn) {
    return 1.0;
}

private double EvaluatePosition(Board board) {

    if (board.IsInCheckmate()) return board.IsWhiteToMove ? double.NegativeInfinity : double.PositiveInfinity;
    
    double score = 0.0;
    PieceList[] allPieceList = board.GetAllPieceLists();
    for (int i=0; i<allPieceList.Length; i++) {
        PieceList pieceList = allPieceList[i];
        foreach (Piece piece in pieceList) {
            double pieceScore = 0.0;
            switch (pieceList.TypeOfPieceInList){
                case PieceType.King:
                    pieceScore += scoreKing(board, piece);
                    break;
                case PieceType.Queen:
                    pieceScore += scoreQueen(board, piece);
                    break;
                case PieceType.Rook:
                    pieceScore += scoreRook(board, piece);
                    break;
                case PieceType.Bishop:
                    pieceScore += scoreBishop(board, piece);
                    break;
                case PieceType.Knight:
                    pieceScore += scoreKnight(board, piece);
                    break;
                case PieceType.Pawn:
                    pieceScore += scorePawn(board, piece);
                    break;
            }

            score += pieceScore * (pieceList.IsWhitePieceList ? 1.0 : -1.0);
        }
        if (pieceList.TypeOfPieceInList == PieceType.King) continue;
    }
    return score;
}
```

Running it against the Marymount Prep Bot, the results were as follows; 

| Result | # |
| --- | --- |
| Wins | 279 |
| Draws | 634 |
| Losses | 87 | 

It's good to see that there's plenty of room for improvement, so this model is going to be a good baseline to build off of. A lot of the draws are repetitions where the bot starts making random moves because none of its moves look any better to the depth 1 search I've hard coded, so a better search function will be the next step.

I have also thought up an extra couple of fun rules I can add to the bot to stick with the theme;

* On wednesdays we wear pink - keep track of the move number modulo 7 to represent the days of the week. On the 3rd day, the queen must wear pink (but she can't), so she can't sit with us, so she has to move.
* She doesn't even go here - When a pawn promotes, she just has a lot of feelings, but for the rest of the game she can't reenter the promotion rank.

# Bot 3 - A better search function

Only having the engine look to depth 1 is obviously not ideal, since the bot will often miss even relatively simple mate in twos. However, the search space quickly blows up if one tries to search any deeper than that. There are a few things I want to implement for this bot;

* Arbitrary calculation depth - Depth 1 is hard coded, the bot needs to traverse the tree as far as it needs
* Evaluation caching - as it is coded now, the bot looks at positions multiple times, so it makes sense to save on computation and cache the results
* Early stopping - if a move chain looks shit, don't go any deeper
* I'm a pusher - move chains involving pawns are always evaluated to maximum depth

I'll do these in order.