<!-- include start from port-number-default.xml.i -->
<leafNode name="port">
  <properties>
    <help>Port number used by connection</help>
    <valueHelp>
      <format>u32:1-65535</format>
      <description>Numeric IP port</description>
    </valueHelp>
    <constraint>
      <validator name="numeric" argument="--range 1-65535"/>
    </constraint>
    <constraintErrorMessage>Port number must be in range 1 to 65535</constraintErrorMessage>
  </properties>
  <defaultValue>{defaultValue}</defaultValue>
</leafNode>
<!-- include end -->
