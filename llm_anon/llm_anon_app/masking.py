import string


def ensemble_choices(ner_dict):
    types = []
    choices = {}
    for name in ner_dict:
        ent_type = ner_dict[name]["entity_type"]
        if ent_type not in types:
            choices[ent_type] = "None"
            types.append(ent_type)

    print("choices: ",choices)
    print("nerdict: ", ner_dict)
    return choices


def complete_masking(entity, word, post_processed_word):
    if entity == "PERCENT":
        return "[REDEACTED]%"
    else:
        return "[REDEACTED]"

def perturbing(entity, word, post_processed_word):
    if entity == "PERSON":
        #TODO
        return "TODO Perturb: "+entity
    elif entity == "ORGANIZATION":
        #TODO
        return "TODO Perturb: "+entity
    elif entity == "GPE":
        #TODO
        return "TODO Perturb: "+entity
    elif entity == "DATE":
        #TODO
        return "TODO Perturb: "+entity
    elif entity == "TIME":
        #TODO
        return "TODO Perturb: "+entity
    elif entity == "MONEY":
        #TODO
        return "TODO Perturb: "+entity
    elif entity == "PERCENT":
        #TODO
        return "TODO Perturb: "+entity
    elif entity == "QUANTITY":
        #TODO
        return "TODO Perturb: "+entity
    elif entity == "ORDINAL":
        #TODO
        return "TODO Perturb: "+entity
    elif entity == "CARDINAL":
        #TODO
        return "TODO Perturb: "+entity
    elif entity == "LOCATION'":
        #TODO
        return "TODO Perturb: "+entity
    else:
        return word

def group_based(entity, word, post_processed_word):
    if entity == "PERSON":
        #TODO
        return "TODO group-based: "+entity
    elif entity == "ORGANIZATION":
        #TODO
        return "TODO group-based: "+entity
    elif entity == "GPE":
        #TODO
        return "TODO group-based: "+entity
    elif entity == "DATE":
        #TODO
        return "TODO group-based: "+entity
    elif entity == "TIME":
        #TODO
        return "TODO group-based: "+entity
    elif entity == "MONEY":
        #TODO
        return "TODO group-based: "+entity
    elif entity == "PERCENT":
        num = int(post_processed_word[:-1])
        return str(round(num, -1)) + "%"
    elif entity == "QUANTITY":
        #TODO
        return "TODO group-based: "+entity
    elif entity == "ORDINAL":
        #TODO
       return "TODO group-based: "+entity
    elif entity == "CARDINAL":
        #TODO
        return "TODO group-based: "+entity
    elif entity == "LOCATION'":
        #TODO
        return "TODO group-based: "+entity
    else:
        return word
#TODO create all mask functions
def mask_main(text, ner_dict, choice_dict):
    #print("ner_dict: ", ner_dict, "  choice_dict: ",choice_dict)
    output_text = ""
    for word in text.split():
        #TODO create post_processing
        post_processed_word = word.lower()
        punc = '''!()-[]{};:'"\,<>./?@#$^&*_~'''

        if word[-1] in punc:
            post_processed_word = post_processed_word[:-1]
        if word[0] == "$":
            post_processed_word = post_processed_word[1:]
        
        if post_processed_word in ner_dict:
            entity = ner_dict[post_processed_word]["entity_type"]
            choice = choice_dict[entity]

            if choice == "Complete Mask":
                post_masked_word = complete_masking(entity, word, post_processed_word)
                post_added_word = word.lower().replace(post_processed_word, post_masked_word) 
                output_text += post_added_word + " "
            elif choice == "Perturb":
                post_masked_word = perturbing(entity, word, post_processed_word)
                post_added_word = word.lower().replace(post_processed_word, post_masked_word) 
                output_text += post_added_word + " "
            elif choice == "Group-based":
                post_masked_word = group_based(entity, word, post_processed_word)
                post_added_word = word.lower().replace(post_processed_word, post_masked_word) 
                output_text += post_added_word + " "
            else:
                output_text += word + " "
        else:
            output_text += word + " "
    return output_text