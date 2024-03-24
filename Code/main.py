from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
import random
import asyncio
from mytoken import token

black = '⚫️'
white = '⚪️'


def enc(board):
    number = 0
    base = 3
    for row in range(8):
        for col in range(8):
            number *= base
            if board.get((row, col)) == black:
                number += 2
            elif board.get((row, col)) == white:
                number += 1
    return str(number)


def dec(number):
    board = {}
    base = 3
    for row in [7, 6, 5, 4, 3, 2, 1, 0]:
        for col in [7, 6, 5, 4, 3, 2, 1, 0]:
            if number % 3 == 2:
                board[(row, col)] = black
            elif number % 3 == 1:
                board[(row, col)] = white
            number //= base
    return board


def board_markup(board):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(board.get((row, col), f' '), callback_data=f'{row}{col}{enc(board)}') for col in range(8)]
        for row in range(8)])


def is_valid_move(board, row, col, color):
    if board.get((row, col)) is not None:
        return False

    other_color = black if color == white else white
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]

    for direction in directions:
        dx, dy = direction
        x, y = row + dx, col + dy
        if (x, y) in board and board[(x, y)] == other_color:
            while (x, y) in board and board[(x, y)] == other_color:
                x += dx
                y += dy
            if (x, y) in board and board[(x, y)] == color:
                return True

    return False


def flip_discs(board, row, col, color):
    other_color = black if color == white else white
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]
    discs_to_flip = []

    for direction in directions:
        dx, dy = direction
        x, y = row + dx, col + dy
        if (x, y) in board and board[(x, y)] == other_color:
            temp = []
            while (x, y) in board and board[(x, y)] == other_color:
                temp.append((x, y))
                x += dx
                y += dy
            if (x, y) in board and board[(x, y)] == color:
                discs_to_flip.extend(temp)

    for disc in discs_to_flip:
        board[disc] = color

    board[(row, col)] = color


def is_game_end(board):
    for row in range(8):
        for col in range(8):
            if is_valid_move(board, row, col, black) or is_valid_move(board, row, col, white):
                return False

    # Check if the board is full
    for row in range(8):
        for col in range(8):
            if board.get((row, col)) is None:
                return False

    return True


def determine_winner(board):
    black_count = sum(1 for disc in board.values() if disc == black)
    white_count = sum(1 for disc in board.values() if disc == white)
    if black_count > white_count:
        return black
    elif white_count > black_count:
        return white
    else:
        return None


async def ai_move(board):
    valid_moves = []
    for row in range(8):
        for col in range(8):
            if is_valid_move(board, row, col, white):
                valid_moves.append((row, col))
    if valid_moves:
        row, col = random.choice(valid_moves)
        flip_discs(board, row, col, white)
        return row, col
    return None, None


async def func(update, context):
    data = update.callback_query.data
    row = int(data[0])
    col = int(data[1])

    board = dec(int(data[2:]))

    if is_valid_move(board, row, col, black):
        flip_discs(board, row, col, black)
        await context.bot.edit_message_text('Wait for AI to make its move.',
                                            reply_markup=board_markup(board),
                                            chat_id=update.callback_query.message.chat_id,
                                            message_id=update.callback_query.message.message_id)

        # Check if the game has ended
        if is_game_end(board):
            winner = determine_winner(board)
            if winner:
                await context.bot.send_message(update.callback_query.message.chat_id,
                                               f'Game over! {winner} wins! Type /gamestart to play again.')
            else:
                await context.bot.send_message(update.callback_query.message.chat_id,
                                               'Game over! It\'s a tie! Type /gamestart to play again.')
        else:
            # AI's move
            await asyncio.sleep(1)
            ai_row, ai_col = await ai_move(board)
            if ai_row is not None and ai_col is not None:
                flip_discs(board, ai_row, ai_col, white)
                await context.bot.edit_message_text('Your turn',
                                                    reply_markup=board_markup(board),
                                                    chat_id=update.callback_query.message.chat_id,
                                                    message_id=update.callback_query.message.message_id)
                # Check if the game has ended
                if is_game_end(board):
                    winner = determine_winner(board)
                    if winner:
                        await context.bot.send_message(update.callback_query.message.chat_id,
                                                       f'Game over! {winner} wins! Type /gamestart to play again.')
                    else:
                        await context.bot.send_message(update.callback_query.message.chat_id,
                                                       'Game over! It\'s a tie! Type /gamestart to play again.')

            else:
                # await context.bot.send_message(update.callback_query.message.chat_id, 'AI cannot make a valid move.')
                await context.bot.edit_message_text('AI cannot make a valid move. It is your turn.',
                                                    reply_markup=board_markup(board),
                                                    chat_id=update.callback_query.message.chat_id,
                                                    message_id=update.callback_query.message.message_id)

                # Check if the player can make a valid move
                if not any(
                        is_valid_move(board, player_row, player_col, black) for player_row in range(8) for player_col in
                        range(8)):
                    # await context.bot.send_message(update.callback_query.message.chat_id,
                    #                                'You cannot make a valid move.')
                    await context.bot.edit_message_text('You cannot make a valid move. It is AI\'s turn.',
                                                        reply_markup=board_markup(board),
                                                        chat_id=update.callback_query.message.chat_id,
                                                        message_id=update.callback_query.message.message_id)

                    # Skip the player's turn
                    await context.bot.edit_message_text('AI\'s turn',
                                                        reply_markup=board_markup(board),
                                                        chat_id=update.callback_query.message.chat_id,
                                                        message_id=update.callback_query.message.message_id)
                    ai_row, ai_col = await ai_move(board)
                    if ai_row is not None and ai_col is not None:
                        flip_discs(board, ai_row, ai_col, white)
                        await context.bot.edit_message_text('Your turn',
                                                            reply_markup=board_markup(board),
                                                            chat_id=update.callback_query.message.chat_id,
                                                            message_id=update.callback_query.message.message_id)
                        # Check if the game has ended
                        if is_game_end(board):
                            winner = determine_winner(board)
                            if winner:
                                await context.bot.send_message(update.callback_query.message.chat_id,
                                                               f'Game over! {winner} wins!'
                                                               f' Type /gamestart to play again.')
                            else:
                                await context.bot.send_message(update.callback_query.message.chat_id,
                                                               'Game over! It\'s a tie! Type /gamestart to play again.')
                    else:
                        await context.bot.send_message(update.callback_query.message.chat_id,
                                                       'AI cannot make a valid move. It is your turn.')
    else:
        await context.bot.answer_callback_query(update.callback_query.id, 'Invalid move. Try again.')


async def start(update, context):
    user = update.effective_user
    await update.message.reply_text(f"Hi {user.name}! Welcome to Reversi. "
                                    f"Type /gameStart to start the game.")


async def gamestart(update, context):
    board = {(3, 3): black, (3, 4): white, (4, 3): white, (4, 4): black}
    await update.message.reply_text('You start', reply_markup=board_markup(board))


def main():
    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("gamestart", gamestart))
    application.add_handler(CallbackQueryHandler(func))

    application.run_polling()


if __name__ == "__main__":
    main()
