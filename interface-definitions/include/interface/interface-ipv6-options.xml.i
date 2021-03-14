<!-- include start from interface/interface-ipv6-options.xml.i -->
<node name="ipv6">
  <properties>
    <help>IPv6 routing parameters</help>
  </properties>
  <children>
    #include <include/interface/ipv6-address.xml.i>
    #include <include/interface/ipv6-disable-forwarding.xml.i>
    #include <include/interface/ipv6-dup-addr-detect-transmits.xml.i>
  </children>
</node>
<!-- include end -->
