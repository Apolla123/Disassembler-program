# основные данные
work_lines = []
number_bit = 0


# делим на биты и превращаем в шестнадцатеричное число
def make_hex(letter, need_0x):
    if len(letter) % 8 != 0:
        letter = '0' * (8 - len(letter) % 8) + letter

    result = []

    for i in range(0, len(letter), 8):
        byte = letter[i:i + 8]
        res = int(byte, 2)

        result.append(hex(res))

    if need_0x:
        return result[-1]
    else:
        return ' '.join([x[2:].zfill(2) for x in result])


# проверяет "накладывается" ли маска на код
def is_matches(code, pattern):
    pattern = str(pattern).replace(" ", "")
    code = str(code).replace(" ", "")
    count_matches = 0

    if len(code) != len(pattern):
        return 0

    for code_letter, pattern_letter in zip(code, pattern):
        if pattern_letter in "01" and code_letter == pattern_letter:
            count_matches += 1
        elif pattern_letter in "01" and code_letter != pattern_letter:
            return 0

    return count_matches


# создаёт список всех букв, которые есть в маске и их цифр, которые совпадают с кодом
def get_letters_in_mask(pattern, code):
    pattern = pattern.replace(" ", "")
    code = code.replace(" ", "")

    letters_in_mask = {}

    for pattern_letter, code_letter in zip(pattern, code):
        if pattern_letter.isalpha():
            if pattern_letter not in letters_in_mask:
                letters_in_mask[pattern_letter] = ""

            letters_in_mask[pattern_letter] += code_letter

    return letters_in_mask


# декодируем
def decode(command, values):
    register_and_bits = {'d', 'r', 'R', 'b'}
    com_with_16 = {'ldi', 'ori', 'cpi', 'andi', 'subi', 'sbci'}
    parts = command.split(maxsplit=1)

    # если nop
    if len(parts) < 2:
        return parts[0]

    list_com = parts[1]

    # сначала ставим временные метки вместо букв. чтобы было удобно заменять
    for letter in values:
        list_com = list_com.replace(letter, f'#{letter}#')

    # потом заменяем метки на готовые значения
    for letter, bits_code in values.items():
        number = int(bits_code, 2)

        if letter in register_and_bits:
            if ('d' == letter or 'r' == letter) and parts[0].lower() in com_with_16:
                value = str(number + 16 if number < 16 else number)
            else:
                value = str(number)
        else:
            value = f'0x{number:02x}'

        list_com = list_com.replace(f'#{letter}#', value)

    return parts[0] + ' ' + list_com


# инвертируем биты
def swich_0_1(line):
    res = ''

    for word in line:
        if word == '0':
            res += '1'
        else:
            res += '0'

    return res


# отдельное декодирование для команд со знаками
def get_sign_comand(bites_code):
    if str(bites_code)[0] == '0':
        first = '+'
    else:
        first = '-'
        bites_code = swich_0_1(bites_code)
        bites_code = bin(int(str(bites_code), 2) + 1)[2:]

    code = int(str(bites_code), 2) * 2
    first += str(code)

    return first


# ищем маску
def find_command(bites_code, finish_result):
    global number_bit

    with open('data/ASM AVR Codes.txt', 'r', encoding='utf-8') as file:
        list_of_comands = {}
        list_of_comands_and_mask = {}

        # Проходимся по файлу и записываем все команды которые подходят
        for line in file.readlines()[2:]:
            command, opisanie, action, cycle, mask_for_code, flags, mask, mask_and, mask_xor = line.split('	')[:-1]
            count_matches = is_matches(bites_code, mask_for_code)
            if count_matches != 0:
                list_of_comands[command] = count_matches
                list_of_comands_and_mask[command] = mask_for_code

                # Меняем название SER на LDI для вывода
                if 'ser Rd' in list_of_comands and 'ldi Rd,K' in list_of_comands:
                    comands_with_max_matches = 'ldi Rd,K'
                else:
                    comands_with_max_matches = max(list_of_comands, key=lambda command: list_of_comands[command])

                mask_for_code_with_max_matches = list_of_comands_and_mask[comands_with_max_matches]
                result = get_letters_in_mask(mask_for_code_with_max_matches, bites_code)

                hex_bit = make_hex(bites_code, need_0x=False)

                lst_bites = hex_bit.split()
                replase_bit = []

                for i in range(0, len(lst_bites), 2):
                    replase_bit.append(lst_bites[i + 1])
                    replase_bit.append(lst_bites[i])

                if comands_with_max_matches in ('rjmp k', 'rcall k') or comands_with_max_matches[0:2] == 'br':
                    finish_comand = comands_with_max_matches.replace(list(result.keys())[0],
                                                                     get_sign_comand(result['k']))
                elif len(mask_for_code_with_max_matches) > 20 and 'k' in result:
                    result['k'] = result['k'][1:] + '0'
                    finish_comand = decode(comands_with_max_matches, result)
                else:
                    finish_comand = decode(comands_with_max_matches, result)

        # Выводим результат
        finish_result.append(f"{hex(number_bit)[2:]}: {' '.join(replase_bit)} {finish_comand}")

        # Нумерация
        number_bit += 4 if len(bites_code) > 20 else 2


# меняем биты местами
def replase_bits(line):
    bits = []
    for i in range(0, len(line), 4):
        bits.append(line[i + 2:i + 4] + line[i:i + 2])
    return bits


# из шестнадцатеричной в двоичную
def make_bit_in_16_to_2(bit_in_16):
    bit_in_10 = int(bit_in_16, 16)
    bit_in_2 = bin(bit_in_10)[2:].zfill(len(bit_in_16) * 4)

    return bit_in_2


def generate_listing(machine_code):
    global number_bit
    number_bit = 0
    finish_result = []

    work_lines = machine_code.strip().splitlines()

    # проходимся по каждой строке
    for work_line in work_lines:
        # убираем первые 9 символов и убираем контрольную сумму, а потом меняем биты местами
        bites = replase_bits(work_line[9:])[:-1]

        while bites:
            # Если нас с 94 значит команда из двух слов
            if bites[0][:2] == '94' and bites[1] != 'CFFF':
                bins_bit = make_bit_in_16_to_2(bites[0] + bites[1])
                bites = bites[2:]
            else:
                bins_bit = make_bit_in_16_to_2(bites[0])
                bites = bites[1:]

            find_command(bins_bit, finish_result)

    return "\n".join(finish_result)