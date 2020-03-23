"""
This is a MODULE docstring
"""

# modification of the `enhanced-subject-verb-object-extraction` package by Rock de Vocht: https://github.com/peter3125/enhanced-subject-verb-object-extraction
#
# Copyright 2017 Peter de Vocht
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# dependency markers for subjects
SUBJECTS = {"nsubj", "nsubjpass", "csubj", "csubjpass", "agent", "expl"}
# dependency markers for objects
OBJECTS = {"dobj", "dative", "attr", "oprd"}
# POS tags that will break adjoining items
BREAKER_POS = {"CCONJ", "VERB"}
# words that are negations
NEGATIONS = {"no", "not", "n't", "never", "none"}

sub_ner_tags = False
obj_ner_tags = False
sub_ent_types = []
obj_ent_types = []


# does dependency set contain any coordinating conjunctions?
def contains_conj(depSet):
    """ 
    This is a docstring.
    """
    return "and" in depSet or "or" in depSet or "nor" in depSet or \
           "but" in depSet or "yet" in depSet or "so" in depSet or "for" in depSet


# get subs joined by conjunctions
def _get_subs_from_conjunctions(subs):
    """ 
    This is a docstring.
    """
    more_subs = []
    for sub in subs:
        # rights is a generator
        rights = list(sub.rights)
        rightDeps = {tok.lower_ for tok in rights}
        if contains_conj(rightDeps):
            if sub_ner_tags:
                more_subs.extend([
                    tok for tok in rights
                    if tok.dep_ in SUBJECTS and tok.ent_type_ in sub_ner_tags
                ])
            else:
                more_subs.extend([
                    tok for tok in rights
                    if tok.dep_ in SUBJECTS or tok.pos_ == "NOUN"
                ])
            if len(more_subs) > 0:
                more_subs.extend(_get_subs_from_conjunctions(more_subs))
    return more_subs


# get objects joined by conjunctions
def _get_objs_from_conjunctions(objs):
    """ 
    This is a docstring.
    """
    more_objs = []
    for obj in objs:
        # rights is a generator
        rights = list(obj.rights)
        rightDeps = {tok.lower_ for tok in rights}
        if contains_conj(rightDeps):
            if obj_ner_tags:
                more_objs.extend([
                    tok for tok in rights
                    if (tok.dep_ in OBJECTS and tok.ent_type_ in obj_ner_tags)
                    or (tok.pos_ == "NOUN" and tok.ent_type_ in obj_ner_tags)
                ])
            else:
                more_objs.extend([
                    tok for tok in rights
                    if tok.dep_ in OBJECTS or tok.pos_ == "NOUN"
                ])
            if len(more_objs) > 0:
                more_objs.extend(_get_objs_from_conjunctions(more_objs))
    return more_objs


# find sub dependencies
def _find_subs(tok):
    """ 
    This is a docstring.
    """
    head = tok.head
    while head.pos_ != "VERB" and head.pos_ != "NOUN" and head.head != head:
        head = head.head
    if head.pos_ == "VERB":
        if sub_ner_tags:
            subs = [
                tok for tok in head.lefts
                if tok.dep_ == "SUB" and tok.ent_type_ in sub_ner_tags
            ]
        else:
            subs = [tok for tok in head.lefts if tok.dep_ == "SUB"]
        if len(subs) > 0:
            verb_negated = _is_negated(head)
            subs.extend(_get_subs_from_conjunctions(subs))
            return subs, verb_negated
        elif head.head != head:
            return _find_subs(head)
    elif sub_ner_tags and head.ent_type_ in sub_ner_tags:
        return [head], _is_negated(tok)
    elif not sub_ner_tags and head.pos_ == "NOUN":
        return [head], _is_negated(tok)
    return [], False


# is the tok set's left or right negated?
def _is_negated(tok):
    """ 
    This is a docstring.
    """
    parts = list(tok.lefts) + list(tok.rights)
    for dep in parts:
        if dep.lower_ in NEGATIONS:
            return True
    return False


# get all the verbs on tokens with negation marker
def _find_svs(tokens):
    """ 
    This is a docstring.
    """
    svs = []
    verbs = [tok for tok in tokens if tok.pos_ == "VERB"]
    for v in verbs:
        subs, verbNegated = _get_all_subs(v)
        if len(subs) > 0:
            for sub in subs:
                svs.append(
                    (sub.orth_, "!" + v.orth_ if verbNegated else v.orth_))
    return svs


# get grammatical objects for a given set of dependencies (including passive sentences)
def _get_objs_from_prepositions(deps, is_pas):
    """ 
    This is a docstring.
    """
    objs = []
    for dep in deps:
        if obj_ner_tags:
            if dep.pos_ == "ADP" and (dep.dep_ == "prep" or
                                      (is_pas and dep.dep_ == "agent")):
                objs.extend([
                    tok for tok in dep.rights
                    if (tok.dep_ in OBJECTS and tok.ent_type_ in obj_ner_tags)
                ])
                #(is_pas and tok.ent_type_ in obj_ner_tags and tok.dep_ == 'pobj')]) #temporarily disabled
        else:
            if dep.pos_ == "ADP" and (dep.dep_ == "prep" or
                                      (is_pas and dep.dep_ == "agent")):
                objs.extend([
                    tok for tok in dep.rights if tok.dep_ in OBJECTS or (
                        tok.pos_ == "PRON" and tok.lower_ == "me") or (
                            is_pas and tok.dep_ == 'pobj')
                ])
    return objs


# get objects from the dependencies using the attribute dependency
# *NOTE* disabled for unknown reason in _get_all_objs, this needs NER option if it should be enabled
def _get_objs_from_attrs(deps, is_pas):
    """ 
    This is a docstring.
    """
    for dep in deps:
        if dep.pos_ == "NOUN" and dep.dep_ == "attr":
            verbs = [tok for tok in dep.rights if tok.pos_ == "VERB"]
            if len(verbs) > 0:
                for v in verbs:
                    rights = list(v.rights)
                    objs = [tok for tok in rights if tok.dep_ in OBJECTS]
                    objs.extend(_get_objs_from_prepositions(rights, is_pas))
                    if len(objs) > 0:
                        return v, objs
    return None, None


# xcomp; open complement - verb has no suject
def _get_obj_from_xcomp(deps, is_pas):
    """ 
    This is a docstring.
    """
    for dep in deps:
        if dep.pos_ == "VERB" and dep.dep_ == "xcomp":
            v = dep
            rights = list(v.rights)
            if obj_ner_tags:
                objs = [
                    tok for tok in rights
                    if tok.dep_ in OBJECTS and tok.ent_type_ in obj_ner_tags
                ]
            else:
                objs = [tok for tok in rights if tok.dep_ in OBJECTS]
            objs.extend(_get_objs_from_prepositions(rights, is_pas))
            if len(objs) > 0:
                return v, objs
    return None, None


# get all functional subjects adjacent to the verb passed in
def _get_all_subs(v):
    """ 
    This is a docstring.
    """
    verb_negated = _is_negated(v)
    if sub_ner_tags:
        subs = [
            tok for tok in v.lefts if tok.dep_ in SUBJECTS
            and tok.ent_type_ in sub_ner_tags and tok.pos_ != "DET"
        ]
    else:
        subs = [
            tok for tok in v.lefts
            if tok.dep_ in SUBJECTS and tok.pos_ != "DET"
        ]
    if len(subs) > 0:
        subs.extend(_get_subs_from_conjunctions(subs))
    else:
        foundSubs, verb_negated = _find_subs(v)
        subs.extend(foundSubs)

    global sub_ent_types
    sub_ent_types = [sub.ent_type_ for sub in subs]

    return subs, verb_negated


# is the token a verb?  (excluding auxiliary verbs)
def _is_non_aux_verb(tok):
    """ 
    This is a docstring.
    """
    return tok.pos_ == "VERB" and (tok.dep_ != "aux" and tok.dep_ != "auxpass")


# return the verb to the right of this verb in a CCONJ relationship if applicable
# returns a tuple, first part True|False and second part the modified verb if True
def _right_of_verb_is_conj_verb(v):
    """ 
    This is a docstring.
    """
    # rights is a generator
    rights = list(v.rights)

    # VERB CCONJ VERB (e.g. he beat and hurt me)
    if len(rights) > 1 and rights[0].pos_ == 'CCONJ':
        for tok in rights[1:]:
            if _is_non_aux_verb(tok):
                return True, tok

    return False, v


# get all objects for an active/passive sentence
def _get_all_objs(v, is_pas):
    """ 
    This is a docstring.
    """
    # rights is a generator
    rights = list(v.rights)
    if obj_ner_tags:
        objs = [
            tok for tok in rights
            if (tok.dep_ in OBJECTS and tok.ent_type_ in obj_ner_tags) or
            (is_pas and tok.dep_ == 'pobj' and tok.ent_type_ in obj_ner_tags)
        ]
    else:
        objs = [
            tok for tok in rights
            if tok.dep_ in OBJECTS or (is_pas and tok.dep_ == 'pobj')
        ]
    objs.extend(_get_objs_from_prepositions(rights, is_pas))

    #potentialNewVerb, potentialNewObjs = _get_objs_from_attrs(rights)
    #if potentialNewVerb is not None and potentialNewObjs is not None and len(potentialNewObjs) > 0:
    #    objs.extend(potentialNewObjs)
    #    v = potentialNewVerb

    potential_new_verb, potential_new_objs = _get_obj_from_xcomp(
        rights, is_pas)
    if potential_new_verb is not None and potential_new_objs is not None and len(
            potential_new_objs) > 0:
        objs.extend(potential_new_objs)
        v = potential_new_verb
    if len(objs) > 0:
        objs.extend(_get_objs_from_conjunctions(objs))

    global obj_ent_types
    obj_ent_types = [obj.ent_type_ for obj in objs]

    return v, objs


# return true if the sentence is passive - at he moment a sentence is assumed passive if it has an auxpass verb
def _is_passive(tokens):
    """ 
    This is a docstring.
    """
    for tok in tokens:
        if tok.dep_ == "auxpass":
            return True
    return False


# resolve a 'that' where/if appropriate
def _get_that_resolution(toks):
    """ 
    This is a docstring.
    """
    for tok in toks:
        if 'that' in [t.orth_ for t in tok.lefts]:
            return tok.head
    return toks


# simple stemmer using lemmas
def _get_lemma(word: str):
    """ 
    This is a docstring.
    """
    tokens = word  #nlp(word)
    if len(tokens) == 1:
        return tokens[0].lemma_
    return word


# print information for displaying all kinds of things of the parse tree
def printDeps(toks):
    """ 
    This is a docstring.
    """
    for tok in toks:
        print(tok.orth_, tok.dep_, tok.pos_, tok.head.orth_,
              [t.orth_ for t in tok.lefts], [t.orth_ for t in tok.rights])


# expand an obj / subj np using its chunk
def expand(item, tokens, visited):
    """ 
    This is a docstring.
    """
    if item.lower_ == 'that':
        item = _get_that_resolution(tokens)

    parts = []

    if hasattr(item, 'lefts'):
        for part in item.lefts:
            if part.pos_ in BREAKER_POS:
                break
            if not part.lower_ in NEGATIONS:
                parts.append(part)

    parts.append(item)

    if hasattr(item, 'rights'):
        for part in item.rights:
            if part.pos_ in BREAKER_POS:
                break
            if not part.lower_ in NEGATIONS:
                parts.append(part)

    if hasattr(parts[-1], 'rights'):
        for item2 in parts[-1].rights:
            if item2.pos_ == "DET" or item2.pos_ == "NOUN":
                if item2.i not in visited:
                    visited.add(item2.i)
                    parts.extend(expand(item2, tokens, visited))
            break

    return parts


# convert a list of tokens to a string
def to_str(tokens):
    """ 
    This is a docstring.
    """
    return ' '.join([item.text for item in tokens])


# find verbs and their subjects / objects to create SVOs, detect passive/active sentences
def findSVOs(tokens, sub_tags=False, obj_tags=False):
    """ 
    This is a docstring.
    """
    global sub_ner_tags
    sub_ner_tags = sub_tags
    global obj_ner_tags
    obj_ner_tags = obj_tags
    svos = []
    is_pas = _is_passive(tokens)
    verbs = [tok for tok in tokens if _is_non_aux_verb(tok)]
    visited = set()  # recursion detection
    sub_ent_types = []
    obj_ent_types = []
    for v in verbs:
        subs, verbNegated = _get_all_subs(v)
        # hopefully there are subs, if not, don't examine this verb any longer
        if len(subs) > 0:
            isConjVerb, conjV = _right_of_verb_is_conj_verb(v)
            if isConjVerb:
                v2, objs = _get_all_objs(conjV, is_pas)
                for sub in subs:
                    for obj in objs:
                        objNegated = _is_negated(obj)
                        if is_pas:  # reverse object / subject for passive
                            svos.append(
                                (to_str(expand(obj, tokens,
                                               visited)), "!" + v.lemma_
                                 if verbNegated or objNegated else v.lemma_,
                                 to_str(expand(sub, tokens, visited))))
                            sub_ent_types.append(sub.ent_type_)
                            obj_ent_types.append(obj.ent_type_)
                            svos.append(
                                (to_str(expand(obj, tokens,
                                               visited)), "!" + v2.lemma_
                                 if verbNegated or objNegated else v2.lemma_,
                                 to_str(expand(sub, tokens, visited))))
                            sub_ent_types.append(sub.ent_type_)
                            obj_ent_types.append(obj.ent_type_)
                        else:
                            svos.append(
                                (to_str(expand(sub, tokens,
                                               visited)), "!" + v.lower_
                                 if verbNegated or objNegated else v.lower_,
                                 to_str(expand(obj, tokens, visited))))
                            sub_ent_types.append(sub.ent_type_)
                            obj_ent_types.append(obj.ent_type_)
                            svos.append(
                                (to_str(expand(sub, tokens,
                                               visited)), "!" + v2.lower_
                                 if verbNegated or objNegated else v2.lower_,
                                 to_str(expand(obj, tokens, visited))))
                            sub_ent_types.append(sub.ent_type_)
                            obj_ent_types.append(obj.ent_type_)
            else:
                v, objs = _get_all_objs(v, is_pas)
                for sub in subs:
                    for obj in objs:
                        objNegated = _is_negated(obj)
                        if is_pas:  # reverse object / subject for passive
                            svos.append(
                                (to_str(expand(obj, tokens,
                                               visited)), "!" + v.lemma_
                                 if verbNegated or objNegated else v.lemma_,
                                 to_str(expand(sub, tokens, visited))))
                            sub_ent_types.append(sub.ent_type_)
                            obj_ent_types.append(obj.ent_type_)
                        else:
                            svos.append(
                                (to_str(expand(sub, tokens,
                                               visited)), "!" + v.lower_
                                 if verbNegated or objNegated else v.lower_,
                                 to_str(expand(obj, tokens, visited))))
                            sub_ent_types.append(sub.ent_type_)
                            obj_ent_types.append(obj.ent_type_)

    return (svos, sub_ent_types, obj_ent_types)
