<?xml version='1.0' encoding='UTF-8'?>
<table xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" id="packageList_table">
    <?python
    import string
    lastLetter = ''
    ?>
    <div py:strip="True" py:for="i, name in enumerate(sorted(packageList.keys(), key=lambda a: a.upper()))">
    <?python
        if name[0].upper() not in string.uppercase:
            currLetter = '#'
        else:
            currLetter = name[0].upper()
    ?>
    <tr class="packageList_section_header" py:if="currLetter != lastLetter">
      <td colspan="3">
      <?python
        lastLetter = currLetter
      ?>
      <h3 class="packageList_section_header" id="troveList_${lastLetter}_target" py:content="lastLetter"/>
      </td>
    </tr>
    <tr id="packageList_trove_row" py:attrs="{'class': (i % 2) and 'odd' or 'even'}" name="row_${name}">
    <td class="packageList_trove_checkbox">
        <input type="checkbox" name="troves" value="${name}" id="checkbox_${name}"/>
    </td>
    <td class="packageList_trove_name"><label for="checkbox_${name}" py:content="name"/></td>
    <td class="packageList_trove_label"><label for="checkbox_${name}" py:content="str(packageList[name][1].trailingLabel())"/></td>
    </tr>
  </div>
</table>
