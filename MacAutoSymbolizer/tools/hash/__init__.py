from .word_frequency import WordFrequency
import hashlib

HASH_FUNC_COUNT = 5


def crash_tag(
    packages: list,
    functions: list
) -> list[str]:
    # content: str = ''
    # hash_list = [a + (b or '') for a, b in zip(punctuated_packages, functions)]

    tag_content: str = ''
    punctuated_packages = WordFrequency.remove_punctuation([(a or '') for a in packages])
    tag_list = [a + '_' + (b or '') for a, b in zip(punctuated_packages, functions)]

    # for x in hash_list[:HASH_FUNC_COUNT]:
    #     if x and x != '<redacted>':
    #         content += ' ' + x

    for x in tag_list[:HASH_FUNC_COUNT]:
        if x and x != '<redacted>':
            tag_content += ' ' + x

    if len(tag_content) > 0:
        freq, app_terminate, pthread_kill = WordFrequency.get_frequency_words(tag_content, top=HASH_FUNC_COUNT)
        tags = [item[0] for item in freq]
        if app_terminate:
            return ['applicationTerminate'] + tags
        if pthread_kill:
            return ['pthread_kill'] + tags
        # freq_content = ' '.join([item[0] for item in freq])
        # return hashlib.md5(freq_content.encode('utf-8')).hexdigest(), tags
        return tags
    # return '0x0', []
    return []
